import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.models import Database
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime ,timedelta
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)



class StartingView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"title": "Starting title", "content": "Starting text"})


class TasksView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self):
        """Helper method to get the model and table with error handling"""
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name="Tasks")
            model = table.get_model()
            return model, table
        except Database.DoesNotExist:
            logger.error("Database 'prathmesh' not found")
            raise ValueError("Database 'prathmesh' not found")
        except Table.DoesNotExist:
            logger.error("Table 'Tasks' not found")
            raise ValueError("Table 'Tasks' not found")
        except Exception as e:
            logger.error(f"Error getting model and table: {str(e)}")
            raise

    def serialize_field_value(self, field_obj, field_value):
        """Enhanced field value serialization with proper link row handling"""
        if field_value is None:
            return None

        field_type = field_obj['type'].type

        try:
            # Handle link row fields
            if field_type == 'link_row':
                # Modern Baserow versions use get_target_table()
                if hasattr(field_obj['type'], 'get_target_table'):
                    target_table = field_obj['type'].get_target_table()
                # Older versions might use link_row_table
                elif hasattr(field_obj['type'], 'link_row_table'):
                    target_table = field_obj['type'].link_row_table
                else:
                    logger.warning(f"Could not determine target table for link row field {field_obj['field'].name}")
                    return []

                if target_table:
                    related_model = target_table.get_model()
                    return {
                        'ids': list(field_value.values_list('id', flat=True)),
                        'objects': [
                            {'id': obj.id, 'name': str(obj)}
                            for obj in field_value.all()[:100]  # Limit to 100 to avoid huge responses
                        ]
                    }
                return []

            # Handle other field types
            if field_type == 'number':
                return float(field_value) if field_value is not None else None
            elif field_type == 'boolean':
                return bool(field_value)
            elif field_type in ['last_modified', 'created_on', 'date']:
                return field_value.isoformat() if hasattr(field_value, 'isoformat') else str(field_value)
            elif field_type == 'multiple_select':
                if isinstance(field_value, list):
                    return [str(v) for v in field_value]
                return [str(field_value)] if field_value else []
            elif field_type == 'single_select':
                if field_value and hasattr(field_value, 'value'):
                    return field_value.value
                return str(field_value) if field_value else None

            return field_value

        except Exception as e:
            logger.error(f"Error serializing field {field_obj['field'].name}: {str(e)}")
            return None

    def get_task_data(self, task):
        """Enhanced task data serialization with proper field handling"""
        try:
            field_objects = task.get_field_objects()
            task_data = {
                'id': task.id,
                'created_on': task.created_on.isoformat() if task.created_on else None,
                'updated_on': task.updated_on.isoformat() if task.updated_on else None
            }

            for field_obj in field_objects:
                field_name = field_obj['field'].name
                field_value = getattr(task, f'field_{field_obj["field"].id}')
                task_data[field_name] = self.serialize_field_value(field_obj, field_value)

            return task_data

        except Exception as e:
            logger.error(f"Error serializing task data: {str(e)}")
            raise ValueError(f"Error serializing task: {str(e)}")

    def get(self, request, task_id=None):
        try:
            model, _ = self.get_model_and_table()

            if task_id:
                task = model.objects.get(id=task_id)
                return Response({
                    "status": "success",
                    "task": self.get_task_data(task)
                })

            tasks = model.objects.all()
            tasks_data = [self.get_task_data(task) for task in tasks]

            return Response({
                "status": "success",
                "count": len(tasks_data),
                "tasks": tasks_data
            })

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Task not found"}, status=404)
        except ValueError as e:
            return Response({"status": "error", "message": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error in GET request: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=500)

    def post(self, request):
        try:
            model, table = self.get_model_and_table()
            data = request.data

            # Validate required fields
            if not data.get('task_name'):
                return Response({
                    "status": "error",
                    "message": "task_name is required"
                }, status=400)

            field_objects = {}
            for field_obj in model.get_field_objects():
                field_name = field_obj['field'].name
                field_objects[field_name] = field_obj

            task_data = {}
            m2m_fields = {}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    if value is not None and value != '':
                        if field_type == 'number':
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                value = None
                        elif field_type == 'boolean':
                            value = str(value).lower() in ('true', '1', 'yes')
                        elif field_type == 'date':
                            try:
                                datetime.strptime(value, '%Y-%m-%d')
                            except ValueError:
                                return Response({
                                    "status": "error",
                                    "message": f"Invalid date format for {field_name}. Use YYYY-MM-DD"
                                }, status=400)
                        elif field_type in ['single_select', 'multiple_select']:
                            select_field = field_obj['field']
                            if field_type == 'multiple_select':
                                if not isinstance(value, list):
                                    value = [value]
                                option_ids = []
                                for val in value:
                                    if isinstance(val, str):
                                        option = select_field.select_options.filter(value=val).first()
                                        if not option:
                                            raise ValueError(f"Option '{val}' not found in field '{field_name}'")
                                        option_ids.append(option.id)
                                    elif isinstance(val, int):
                                        if not select_field.select_options.filter(id=val).exists():
                                            raise ValueError(f"Option ID {val} not found in field '{field_name}'")
                                        option_ids.append(val)
                                m2m_fields[f'field_{field_id}'] = option_ids
                                continue
                            else:  # single_select
                                if isinstance(value, str):
                                    option = select_field.select_options.filter(value=value).first()
                                    if not option:
                                        raise ValueError(f"Option '{value}' not found in field '{field_name}'")
                                    value = option.id
                                elif isinstance(value, int):
                                    if not select_field.select_options.filter(id=value).exists():
                                        raise ValueError(f"Option ID {value} not found in field '{field_name}'")
                        elif field_type == 'link_row':
                            # Handle link row field updates
                            if not isinstance(value, list):
                                value = [value]

                            # Convert to integers if they're string IDs
                            link_ids = []
                            for val in value:
                                try:
                                    link_ids.append(int(val))
                                except (ValueError, TypeError):
                                    continue

                            m2m_fields[f'field_{field_id}'] = link_ids
                            continue

                    task_data[f'field_{field_id}'] = value

            # Create the task
            task = model.objects.create(**task_data)

            # Handle many-to-many relationships after creation
            for m2m_field_name, value in m2m_fields.items():
                m2m_field = getattr(task, m2m_field_name)
                m2m_field.set(value)

            return Response({
                "status": "success",
                "message": "Task created successfully",
                "task": self.get_task_data(task)
            }, status=201)

        except ValueError as e:
            logger.error(f"Validation error creating task: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return Response({
                "status": "error",
                "message": "Failed to create task",
                "error": str(e)
            }, status=500)

    def put(self, request, task_id):
        try:
            model, table = self.get_model_and_table()
            task = model.objects.get(id=task_id)
            data = request.data

            field_objects = {}
            for field_obj in model.get_field_objects():
                field_name = field_obj['field'].name
                field_objects[field_name] = field_obj

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    if value is not None and value != '':
                        if field_type == 'number':
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                value = None
                        elif field_type == 'boolean':
                            value = str(value).lower() in ('true', '1', 'yes')
                        elif field_type == 'date':
                            try:
                                datetime.strptime(value, '%Y-%m-%d')
                            except ValueError:
                                return Response({
                                    "status": "error",
                                    "message": f"Invalid date format for {field_name}. Use YYYY-MM-DD"
                                }, status=400)
                        elif field_type == 'multiple_select':
                            select_field = field_obj['field']
                            if not isinstance(value, list):
                                value = [value]
                            option_ids = []
                            for val in value:
                                if isinstance(val, str):
                                    option = select_field.select_options.filter(value=val).first()
                                    if not option:
                                        raise ValueError(f"Option '{val}' not found in field '{field_name}'")
                                    option_ids.append(option.id)
                                elif isinstance(val, int):
                                    if not select_field.select_options.filter(id=val).exists():
                                        raise ValueError(f"Option ID {val} not found in field '{field_name}'")
                                    option_ids.append(val)
                            m2m_field = getattr(task, f'field_{field_id}')
                            m2m_field.set(option_ids)
                            continue
                        elif field_type == 'link_row':
                            # Handle link row field updates
                            if not isinstance(value, list):
                                value = [value]

                            # Convert to integers if they're string IDs
                            link_ids = []
                            for val in value:
                                try:
                                    link_ids.append(int(val))
                                except (ValueError, TypeError):
                                    continue

                            m2m_field = getattr(task, f'field_{field_id}')
                            m2m_field.set(link_ids)
                            continue

                    setattr(task, f'field_{field_id}', value)

            task.save()

            return Response({
                "status": "success",
                "message": "Task updated successfully",
                "task": self.get_task_data(task)
            })

        except model.DoesNotExist:
            logger.error(f"Task not found with ID: {task_id}")
            return Response({
                "status": "error",
                "message": "Task not found"
            }, status=404)
        except ValueError as e:
            logger.error(f"Validation error updating task: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            return Response({
                "status": "error",
                "message": "Failed to update task",
                "error": str(e)
            }, status=500)

    def delete(self, request, task_id):
        try:
            model, table = self.get_model_and_table()
            task = model.objects.get(id=task_id)
            task.delete()

            return Response({
                "status": "success",
                "message": "Task deleted successfully"
            }, status=200)

        except model.DoesNotExist:
            logger.error(f"Task not found with ID: {task_id}")
            return Response({
                "status": "error",
                "message": "Task not found"
            }, status=404)
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            return Response({
                "status": "error",
                "message": "Failed to delete task",
                "error": str(e)
            }, status=500)

class CategoriesView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self):
        """Helper to get the Categories model from Baserow with better error handling"""
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name="Categories")
            return table.get_model(), table
        except Database.DoesNotExist:
            logger.error("Database 'prathmesh' not found", exc_info=True)
            raise ValidationError({
                "status": "error",
                "message": "Database not found",
                "code": "database_not_found"
            })
        except Table.DoesNotExist:
            logger.error("Table 'Categories' not found", exc_info=True)
            raise ValidationError({
                "status": "error",
                "message": "Categories table not found",
                "code": "table_not_found"
            })
        except Exception as e:
            logger.error(f"Unexpected error getting model: {str(e)}", exc_info=True)
            raise ValidationError({
                "status": "error",
                "message": "Internal server error",
                "code": "server_error"
            })

    def serialize_field_value(self, field_obj, field_value):
        """More robust field value serialization with detailed error handling"""
        if field_value is None:
            return None

        field_type = field_obj['type'].type

        try:
            if field_type == 'single_select':
                try:
                    option = field_obj['field'].select_options.get(id=field_value)
                    return {
                        'id': option.id,
                        'value': option.value,
                        'color': option.color
                    }
                except Exception as e:
                    logger.warning(f"Failed to serialize select option {field_value}: {str(e)}")
                    return None

            elif field_type == 'link_row':
                try:
                    related_model = field_obj['type'].link_row_table.get_model()
                    return [
                        {
                            'id': item.id,
                            'name': getattr(item, 'field_1', 'Unknown')
                        } for item in field_value.all()
                    ]
                except Exception as e:
                    logger.error(f"Failed to serialize link_row field: {str(e)}")
                    return []

            elif field_type == 'number':
                try:
                    return float(field_value)
                except (TypeError, ValueError):
                    logger.warning(f"Invalid number value: {field_value}")
                    return None

            elif field_type == 'boolean':
                return bool(field_value)

            elif field_type in ['created_on', 'updated_on', 'last_modified']:
                try:
                    return field_value.isoformat() if field_value else None
                except AttributeError:
                    logger.warning(f"Invalid date value: {field_value}")
                    return None

            return field_value

        except Exception as e:
            logger.error(f"Unexpected error serializing field: {str(e)}")
            return None

    def get_category_data(self, category):
        """More resilient category data serialization"""
        try:
            field_objects = category.get_field_objects()
            category_data = {
                'id': category.id,
                'created_on': category.created_on.isoformat() if category.created_on else None,
                'updated_on': category.updated_on.isoformat() if category.updated_on else None
            }

            for field_obj in field_objects:
                field_name = field_obj['field'].name
                try:
                    field_value = getattr(category, f'field_{field_obj["field"].id}')
                    category_data[field_name] = self.serialize_field_value(field_obj, field_value)
                except Exception as e:
                    logger.error(f"Error processing field {field_name}: {str(e)}")
                    category_data[field_name] = None

            return category_data

        except Exception as e:
            logger.error(f"Failed to serialize category data: {str(e)}", exc_info=True)
            raise ValidationError({
                "status": "error",
                "message": "Could not process category data",
                "code": "serialization_error",
                "details": str(e)
            })

    def get(self, request, category_id=None):
        """Enhanced GET with better error responses"""
        try:
            model, _ = self.get_model_and_table()

            if category_id:
                try:
                    category = model.objects.get(id=category_id)
                    return Response({
                        "status": "success",
                        "category": self.get_category_data(category)
                    })
                except model.DoesNotExist:
                    return Response({
                        "status": "error",
                        "message": "Category not found",
                        "code": "not_found"
                    }, status=404)

            categories = model.objects.all()
            return Response({
                "status": "success",
                "count": categories.count(),
                "categories": [self.get_category_data(c) for c in categories]
            })

        except Exception as e:
            logger.error(f"GET request failed: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": "Failed to retrieve categories",
                "code": "server_error",
                "details": str(e)
            }, status=500)

    def prepare_category_data(self, model, data):
        """More robust data preparation with validation"""
        if not isinstance(data, dict):
            raise ValidationError({
                "status": "error",
                "message": "Invalid input data format",
                "code": "invalid_input"
            })

        field_map = {
            field_obj['field'].name: {
                'id': field_obj['field'].id,
                'type': field_obj['type'].type,
                'field': field_obj['field']
            }
            for field_obj in model.get_field_objects()
        }

        category_data = {}
        for field_name, value in data.items():
            if field_name not in field_map:
                logger.warning(f"Ignoring unknown field: {field_name}")
                continue

            field_info = field_map[field_name]
            field_key = f'field_{field_info["id"]}'

            # Handle special field types
            if field_info['type'] == 'link_row':
                if not isinstance(value, (list, int, str)):
                    raise ValidationError({
                        "status": "error",
                        "message": f"Invalid value for {field_name}",
                        "code": "invalid_field_value"
                    })
                category_data[field_key] = [value] if isinstance(value, (int, str)) else value
            elif field_info['type'] == 'single_select':
                if isinstance(value, dict):
                    category_data[field_key] = value.get('id', value)
                else:
                    category_data[field_key] = value
            else:
                category_data[field_key] = value

        return category_data

    def post(self, request):
        """Improved POST with better validation"""
        try:
            model, table = self.get_model_and_table()

            if not request.data.get('name'):
                raise ValidationError({
                    "status": "error",
                    "message": "Name is required",
                    "code": "missing_field"
                })

            category_data = self.prepare_category_data(model, request.data)
            category = model.objects.create(**category_data)

            return Response({
                "status": "success",
                "message": "Category created successfully",
                "category": self.get_category_data(category)
            }, status=201)

        except ValidationError as e:
            logger.warning(f"Validation error: {str(e.detail)}")
            return Response(e.detail, status=400)
        except Exception as e:
            logger.error(f"Create failed: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": "Failed to create category",
                "code": "create_failed",
                "details": str(e)
            }, status=500)

    def put(self, request, category_id):
        """Enhanced PUT operation"""
        try:
            model, table = self.get_model_and_table()
            category = model.objects.get(id=category_id)

            category_data = self.prepare_category_data(model, request.data)
            for field_key, value in category_data.items():
                setattr(category, field_key, value)

            category.save()

            return Response({
                "status": "success",
                "message": "Category updated successfully",
                "category": self.get_category_data(category)
            })

        except model.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Category not found",
                "code": "not_found"
            }, status=404)
        except ValidationError as e:
            return Response(e.detail, status=400)
        except Exception as e:
            logger.error(f"Update failed: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": "Failed to update category",
                "code": "update_failed",
                "details": str(e)
            }, status=500)

    def delete(self, request, category_id):
        """More robust DELETE operation"""
        try:
            model, _ = self.get_model_and_table()
            category = model.objects.get(id=category_id)

            # Store data for response before deletion
            deleted_data = self.get_category_data(category)
            category.delete()

            return Response({
                "status": "success",
                "message": "Category deleted successfully",
                "deleted_category": deleted_data
            })

        except model.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Category not found",
                "code": "not_found"
            }, status=404)
        except Exception as e:
            logger.error(f"Delete failed: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": "Failed to delete category",
                "code": "delete_failed",
                "details": str(e)
            }, status=500)



from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class UserRegisterView(APIView):
    permission_classes = (AllowAny,)

    # Corrected FIELD_MAPPING based on your error
    FIELD_MAPPING = {
        'username': 'field_88',  # Text field
        'email': 'field_89',  # Text field
        'password': 'field_93',  # <-- This was the problem field (should be text/long text)
        'first_name': 'field_91',  # Text field
        'last_name': 'field_92',  # Text field
        'is_active': 'field_90',  # <-- Changed to boolean field
        'roles': 'field_94',  # Multiple select field
        'last_login': 'field_95'  # Date field
    }

    def get_model(self):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name="Users")
            return table.get_model()
        except Exception as e:
            logger.error(f"Error getting Users model: {str(e)}")
            raise ValueError(f"Error accessing database: {str(e)}")

    def post(self, request):
        try:
            model = self.get_model()
            data = request.data

            # Debug: Print actual field types
            fields = model._meta.get_fields()
            field_types = {f.name: f.get_internal_type() for f in fields if hasattr(f, 'get_internal_type')}
            logger.debug(f"Actual field types: {field_types}")

            # Validate required fields
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return Response({
                        "status": "error",
                        "message": f"{field} is required"
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Check for existing user
            if model.objects.filter(**{self.FIELD_MAPPING['username']: data['username']}).exists():
                return Response({
                    "status": "error",
                    "message": "Username already exists"
                }, status=status.HTTP_409_CONFLICT)

            if model.objects.filter(**{self.FIELD_MAPPING['email']: data['email']}).exists():
                return Response({
                    "status": "error",
                    "message": "Email already exists"
                }, status=status.HTTP_409_CONFLICT)

            # Prepare user data with correct field mapping
            user_data = {
                self.FIELD_MAPPING['username']: data['username'],
                self.FIELD_MAPPING['email']: data['email'],
                self.FIELD_MAPPING['password']: make_password(data['password']),
                self.FIELD_MAPPING['first_name']: data.get('first_name', ''),
                self.FIELD_MAPPING['last_name']: data.get('last_name', ''),
                self.FIELD_MAPPING['is_active']: True,  # Must be boolean
                self.FIELD_MAPPING['roles']: ["user"]  # Must be array for multiple select
            }

            # Create user
            user = model.objects.create(**user_data)

            return Response({
                "status": "success",
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "username": getattr(user, self.FIELD_MAPPING['username']),
                    "email": getattr(user, self.FIELD_MAPPING['email'])
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)

            # Get actual field names and types for debugging
            fields_info = []
            if 'model' in locals():
                fields = model._meta.get_fields()
                fields_info = [f"{f.name} ({f.get_internal_type()})" for f in fields if hasattr(f, 'get_internal_type')]

            return Response({
                "status": "error",
                "message": "Registration failed",
                "error": str(e),
                "field_mapping": self.FIELD_MAPPING,
                "actual_fields": fields_info
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    permission_classes = (AllowAny,)

    # Updated to match the corrected FIELD_MAPPING
    FIELD_MAPPING = {
        'username': 'field_88',
        'password': 'field_93',
        'is_active': 'field_90',
        'last_login': 'field_95',
        'roles': 'field_94',
        'email': 'field_89'
    }

    def get_model(self):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name="Users")
            return table.get_model()
        except Exception as e:
            logger.error(f"Error getting Users model: {str(e)}")
            raise

    def post(self, request):
        try:
            model = self.get_model()
            data = request.data

            if not data.get('username') or not data.get('password'):
                return Response({
                    "status": "error",
                    "message": "Username and password are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            user = model.objects.filter(**{self.FIELD_MAPPING['username']: data['username']}).first()
            if not user:
                return Response({
                    "status": "error",
                    "message": "Invalid credentials"
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not check_password(data['password'], getattr(user, self.FIELD_MAPPING['password'])):
                return Response({
                    "status": "error",
                    "message": "Invalid credentials"
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not getattr(user, self.FIELD_MAPPING['is_active']):
                return Response({
                    "status": "error",
                    "message": "Account is inactive"
                }, status=status.HTTP_403_FORBIDDEN)

            # Update last login
            setattr(user, self.FIELD_MAPPING['last_login'], datetime.now())
            user.save()

            # Create session
            request.session['user_id'] = user.id
            request.session.set_expiry(86400)

            return Response({
                "status": "success",
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": getattr(user, self.FIELD_MAPPING['username']),
                    "email": getattr(user, self.FIELD_MAPPING['email']),
                    "roles": getattr(user, self.FIELD_MAPPING['roles'], [])
                }
            })

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({
                "status": "error",
                "message": "Login failed",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class UserLogoutView(APIView):
    def post(self, request):
        try:
            if 'user_id' in request.session:
                user_id = request.session['user_id']
                request.session.flush()
                logger.info(f"User {user_id} logged out")

            return Response({
                "status": "success",
                "message": "Logged out successfully"
            })
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({
                "status": "error",
                "message": "Logout failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class BaseBaserowView(APIView):
    """Base view for Baserow table operations"""

    DATABASE_NAME = "prathmesh"

    def get_model_and_table(self,cources):
        """Helper method to get the model and table with error handling"""
        try:
            database = Database.objects.get(name=self.DATABASE_NAME)
            table = Table.objects.get(database=database, name=cources)
            model = table.get_model()
            return model, table
        except Database.DoesNotExist:
            logger.error(f"Database '{self.DATABASE_NAME}' not found")
            raise ValueError(f"Database '{self.DATABASE_NAME}' not found")
        except Table.DoesNotExist:
            logger.error(f"Table '{cources}' not found")
            raise ValueError(f"Table '{cources}' not found")
        except Exception as e:
            logger.error(f"Error getting model and table: {str(e)}")
            raise

    def serialize_field_value(self, field_obj, field_value):
        """Enhanced field value serialization with proper link row handling"""
        if field_value is None:
            return None

        field_type = field_obj['type'].type

        try:
            # Handle link row fields
            if field_type == 'link_row':
                target_table = getattr(field_obj['type'], 'get_target_table', lambda: None)()
                if not target_table:
                    target_table = getattr(field_obj['type'], 'link_row_table', None)

                if target_table:
                    related_model = target_table.get_model()
                    return {
                        'ids': list(field_value.values_list('id', flat=True)),
                        'objects': [
                            {'id': obj.id, 'name': str(obj)}
                            for obj in field_value.all()[:100]  # Limit to 100
                        ]
                    }
                return []

            # Handle other field types
            if field_type == 'number':
                return float(field_value) if field_value is not None else None
            elif field_type == 'boolean':
                return bool(field_value)
            elif field_type in ['last_modified', 'created_on', 'date']:
                return field_value.isoformat() if hasattr(field_value, 'isoformat') else str(field_value)
            elif field_type == 'multiple_select':
                if isinstance(field_value, list):
                    return [str(v) for v in field_value]
                return [str(field_value)] if field_value else []
            elif field_type == 'single_select':
                if field_value and hasattr(field_value, 'value'):
                    return field_value.value
                return str(field_value) if field_value else None

            return field_value

        except Exception as e:
            logger.error(f"Error serializing field {field_obj['field'].name}: {str(e)}")
            return None

    def get_object_data(self, obj):
        """Enhanced object data serialization with proper field handling"""
        try:
            field_objects = obj.get_field_objects()
            obj_data = {
                'id': obj.id,
                'created_on': obj.created_on.isoformat() if obj.created_on else None,
                'updated_on': obj.updated_on.isoformat() if obj.updated_on else None
            }

            for field_obj in field_objects:
                field_name = field_obj['field'].name
                field_value = getattr(obj, f'field_{field_obj["field"].id}')
                obj_data[field_name] = self.serialize_field_value(field_obj, field_value)

            return obj_data

        except Exception as e:
            logger.error(f"Error serializing object data: {str(e)}")
            raise ValueError(f"Error serializing object: {str(e)}")


class CourseView(BaseBaserowView):
    permission_classes = (AllowAny,)

    def get(self, request, course_id=None):
        try:
            model, _ = self.get_model_and_table("Courses")

            if course_id:
                course = model.objects.get(id=course_id)
                return Response({
                    "status": "success",
                    "course": self.get_object_data(course)
                })

            courses = model.objects.all()
            courses_data = [self.get_object_data(course) for course in courses]

            return Response({
                "status": "success",
                "count": len(courses_data),
                "courses": courses_data
            })

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Course not found"}, status=404)
        except ValueError as e:
            return Response({"status": "error", "message": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error in GET request: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=500)


class LessonView(BaseBaserowView):
    permission_classes = (AllowAny,)

    def get(self, request, course_id=None, lesson_id=None):
        try:
            model, _ = self.get_model_and_table("Lessons")

            if lesson_id:
                lesson = model.objects.get(id=lesson_id)
                return Response({
                    "status": "success",
                    "lesson": self.get_object_data(lesson)
                })

            # Filter lessons by course if course_id provided
            if course_id:
                lessons = model.objects.filter(field_1=[course_id])  # field_1 should be the link to Courses
            else:
                lessons = model.objects.all()

            lessons_data = [self.get_object_data(lesson) for lesson in lessons]

            return Response({
                "status": "success",
                "count": len(lessons_data),
                "lessons": lessons_data
            })

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Lesson not found"}, status=404)
        except ValueError as e:
            return Response({"status": "error", "message": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error in GET request: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=500)


class EnrollmentView(BaseBaserowView):
    permission_classes = (AllowAny,)

    def post(self, request, course_id):
        try:
            # Get the Courses and Enrollments tables
            course_model, _ = self.get_model_and_table("Courses")
            enrollment_model, _ = self.get_model_and_table("Enrollments")

            # Check if course exists
            course = course_model.objects.get(id=course_id)

            # Check if user is already enrolled
            existing_enrollment = enrollment_model.objects.filter(
                field_1=request.user.id,  # field_1 should be link to Users
                field_2=course_id  # field_2 should be link to Courses
            ).first()

            if existing_enrollment:
                return Response({
                    "status": "success",
                    "message": "Already enrolled",
                    "enrollment": self.get_object_data(existing_enrollment)
                }, status=200)

            # Create new enrollment
            enrollment_data = {
                'field_1': [request.user.id],  # User
                'field_2': [course_id],  # Course
                'field_3': 0,  # Progress
                'field_4': False,  # Completed
                'field_5': datetime.now().isoformat()  # Enrolled date
            }

            enrollment = enrollment_model.objects.create(**enrollment_data)

            return Response({
                "status": "success",
                "message": "Enrolled successfully",
                "enrollment": self.get_object_data(enrollment)
            }, status=201)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Course not found"}, status=404)
        except Exception as e:
            logger.error(f"Error enrolling: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=500)


class UserProgressView(BaseBaserowView):
    permission_classes = (AllowAny,)

    def post(self, request, lesson_id):
        try:
            # Get the Lessons and UserProgress tables
            lesson_model, _ = self.get_model_and_table("Lessons")
            progress_model, _ = self.get_model_and_table("UserProgress")

            # Check if lesson exists and get course
            lesson = lesson_model.objects.get(id=lesson_id)
            course_id = lesson.field_1[0]  # Assuming field_1 links to Courses

            # Check if user is enrolled in the course
            enrollment_model, _ = self.get_model_and_table("Enrollments")
            enrollment = enrollment_model.objects.filter(
                field_1=request.user.id,
                field_2=course_id
            ).first()

            if not enrollment:
                return Response({
                    "status": "error",
                    "message": "Not enrolled in this course"
                }, status=403)

            # Check if progress already exists
            existing_progress = progress_model.objects.filter(
                field_1=request.user.id,  # User
                field_2=lesson_id  # Lesson
            ).first()

            if existing_progress:
                return Response({
                    "status": "success",
                    "message": "Already completed",
                    "progress": self.get_object_data(existing_progress)
                }, status=200)

            # Create new progress record
            progress_data = {
                'field_1': [request.user.id],  # User
                'field_2': [lesson_id],  # Lesson
                'field_3': True,  # Completed
                'field_4': datetime.now().isoformat()  # Completed date
            }

            progress = progress_model.objects.create(**progress_data)

            # Update enrollment progress
            total_lessons = lesson_model.objects.filter(field_1=course_id).count()
            completed_lessons = progress_model.objects.filter(
                field_1=request.user.id,
                field_2__in=[l.id for l in lesson_model.objects.filter(field_1=course_id)]
            ).count()

            new_progress = int((completed_lessons / total_lessons) * 100)
            enrollment.field_3 = new_progress  # Progress field

            if new_progress == 100:
                enrollment.field_4 = True  # Completed field

            enrollment.save()

            return Response({
                "status": "success",
                "message": "Progress updated",
                "progress": self.get_object_data(progress),
                "course_progress": new_progress
            }, status=201)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Lesson not found"}, status=404)
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=500)



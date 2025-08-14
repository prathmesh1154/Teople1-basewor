import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.models import Database
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime ,timedelta
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from baserow.contrib.database.fields.models import Field
from django.db import transaction

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



class CoursesView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Courses"):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def get_relation_field_id(self, table_name, target_table="Courses"):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name=table_name)

            link_fields = table.field_set.filter(type='link_row')

            # First try exact matches where link_row_table is target_table
            for field in link_fields:
                if field.link_row_table.name == target_table:
                    return f'field_{field.id}'

            # Fallback: try common field names
            common_names = ['course', 'parent_course', 'related_course', 'course_link']
            for name in common_names:
                try:
                    field = table.field_set.get(name=name, type='link_row')
                    if field.link_row_table.name == target_table:
                        return f'field_{field.id}'
                except Exception:
                    continue

            # Last fallback: return first link field linking to target_table if any
            for field in link_fields:
                if field.link_row_table.name == target_table:
                    return f'field_{field.id}'

            logger.error(f"No link_row field found in {table_name} linking to {target_table}")
            return None

        except Exception as e:
            logger.error(f"Error finding relation field in {table_name}: {str(e)}")
            return None

    def get_course_data(self, course):
        try:
            field_objects = course.get_field_objects()
            course_data = {
                'id': course.id,
                'order': str(course.order) if hasattr(course, 'order') else None,
                'created_on': course.created_on.isoformat() if course.created_on else None,
                'updated_on': course.updated_on.isoformat() if course.updated_on else None
            }

            for field_object in field_objects:
                field_name = field_object['field'].name
                try:
                    field_value = getattr(course, f'field_{field_object["field"].id}')
                    course_data[field_name] = self.convert_field_value(
                        field_value,
                        field_object['type'].type
                    )
                except Exception as e:
                    logger.warning(f"Couldn't get field {field_name} value: {str(e)}")
                    course_data[field_name] = None

            return course_data
        except Exception as e:
            logger.error(f"Error formatting course data: {str(e)}")
            raise

    def convert_field_value(self, value, field_type):
        if value is None:
            return None

        if field_type == 'number':
            return float(value)
        elif field_type == 'boolean':
            return bool(value)
        elif field_type in ['date', 'last_modified', 'created_on']:
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        elif field_type == 'link_row':
            if hasattr(value, 'all'):
                return [{'id': obj.id, 'value': str(obj)} for obj in value.all()]
            elif hasattr(value, 'id'):
                return {'id': value.id, 'value': str(value)}
            return None
        else:
            return value

    def get(self, request, course_id=None):
        try:
            model, _ = self.get_model_and_table()
            if course_id:
                course = model.objects.get(id=course_id)
                course_data = self.get_course_data(course)
                return Response({"status": "success", "course": course_data})

            courses = model.objects.all()
            return Response({
                "status": "success",
                "count": courses.count(),
                "courses": [self.get_course_data(course) for course in courses]
            })
        except model.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)
        except Exception as e:
            logger.error(f"Error in CoursesView GET: {str(e)}")
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        try:
            model, _ = self.get_model_and_table()
            data = request.data

            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
            course_data = {}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type
                    course_data[f'field_{field_id}'] = self.convert_field_value(value, field_type)

            course = model.objects.create(**course_data)
            return Response({
                "status": "success",
                "message": "Course created successfully",
                "course": self.get_course_data(course)
            }, status=201)
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            return Response({"error": str(e)}, status=400)

    def put(self, request, course_id):
        try:
            model, _ = self.get_model_and_table()
            course = model.objects.get(id=course_id)
            data = request.data

            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type
                    setattr(course, f'field_{field_id}', self.convert_field_value(value, field_type))

            course.save()
            return Response({
                "status": "success",
                "message": "Course updated successfully",
                "course": self.get_course_data(course)
            })
        except model.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}")
            return Response({"error": str(e)}, status=400)

    def delete(self, request, course_id):
        try:
            model, _ = self.get_model_and_table()
            course = model.objects.get(id=course_id)
            course.delete()
            return Response({
                "status": "success",
                "message": "Course deleted successfully"
            })
        except model.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)
        except Exception as e:
            logger.error(f"Error deleting course: {str(e)}")
            return Response({"error": str(e)}, status=400)


class LessonsView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Lessons"):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def get_relation_field_id(self, table_name, target_table="Lessons"):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name=table_name)

            link_fields = table.field_set.filter(type='link_row')

            # First try exact matches where link_row_table is target_table
            for field in link_fields:
                if field.link_row_table.name == target_table:
                    return f'field_{field.id}'

            # Fallback: try common field names
            common_names = ['lesson', 'parent_lesson', 'related_lesson', 'lesson_link']
            for name in common_names:
                try:
                    field = table.field_set.get(name=name, type='link_row')
                    if field.link_row_table.name == target_table:
                        return f'field_{field.id}'
                except Exception:
                    continue

            # Last fallback: return first link field linking to target_table if any
            for field in link_fields:
                if field.link_row_table.name == target_table:
                    return f'field_{field.id}'

            logger.error(f"No link_row field found in {table_name} linking to {target_table}")
            return None

        except Exception as e:
            logger.error(f"Error finding relation field in {table_name}: {str(e)}")
            return None

    def get_lesson_data(self, lesson):
        try:
            field_objects = lesson.get_field_objects()
            lesson_data = {
                'id': lesson.id,
                'order': str(lesson.order) if hasattr(lesson, 'order') else None,
                'created_on': lesson.created_on.isoformat() if lesson.created_on else None,
                'updated_on': lesson.updated_on.isoformat() if lesson.updated_on else None
            }

            for field_object in field_objects:
                field_name = field_object['field'].name
                try:
                    field_value = getattr(lesson, f'field_{field_object["field"].id}')
                    lesson_data[field_name] = self.convert_field_value(
                        field_value,
                        field_object['type'].type
                    )
                except Exception as e:
                    logger.warning(f"Couldn't get field {field_name} value: {str(e)}")
                    lesson_data[field_name] = None

            return lesson_data
        except Exception as e:
            logger.error(f"Error formatting lesson data: {str(e)}")
            raise

    def convert_field_value(self, value, field_type):
        if value is None:
            return None

        if field_type == 'number':
            return float(value)
        elif field_type == 'boolean':
            return bool(value)
        elif field_type in ['date', 'last_modified', 'created_on']:
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        elif field_type == 'link_row':
            if hasattr(value, 'all'):
                return [{'id': obj.id, 'value': str(obj)} for obj in value.all()]
            elif hasattr(value, 'id'):
                return {'id': value.id, 'value': str(value)}
            return None
        else:
            return value

    def get(self, request, lesson_id=None):
        try:
            model, _ = self.get_model_and_table()
            if lesson_id:
                lesson = model.objects.get(id=lesson_id)
                lesson_data = self.get_lesson_data(lesson)
                return Response({"status": "success", "lesson": lesson_data})

            lessons = model.objects.all()
            return Response({
                "status": "success",
                "count": lessons.count(),
                "lessons": [self.get_lesson_data(lesson) for lesson in lessons]
            })
        except model.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=404)
        except Exception as e:
            logger.error(f"Error in LessonsView GET: {str(e)}")
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        try:
            model, _ = self.get_model_and_table()
            data = request.data

            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
            lesson_data = {}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type
                    lesson_data[f'field_{field_id}'] = self.convert_field_value(value, field_type)

            lesson = model.objects.create(**lesson_data)
            return Response({
                "status": "success",
                "message": "Lesson created successfully",
                "lesson": self.get_lesson_data(lesson)
            }, status=201)
        except Exception as e:
            logger.error(f"Error creating lesson: {str(e)}")
            return Response({"error": str(e)}, status=400)

    def put(self, request, lesson_id):
        try:
            model, _ = self.get_model_and_table()
            lesson = model.objects.get(id=lesson_id)
            data = request.data

            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type
                    setattr(lesson, f'field_{field_id}', self.convert_field_value(value, field_type))

            lesson.save()
            return Response({
                "status": "success",
                "message": "Lesson updated successfully",
                "lesson": self.get_lesson_data(lesson)
            })
        except model.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=404)
        except Exception as e:
            logger.error(f"Error updating lesson: {str(e)}")
            return Response({"error": str(e)}, status=400)

    def delete(self, request, lesson_id):
        try:
            model, _ = self.get_model_and_table()
            lesson = model.objects.get(id=lesson_id)
            lesson.delete()
            return Response({
                "status": "success",
                "message": "Lesson deleted successfully"
            })
        except model.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=404)
        except Exception as e:
            logger.error(f"Error deleting lesson: {str(e)}")
            return Response({"error": str(e)}, status=400)


class EnrollmentsView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Enrollments"):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Database.DoesNotExist:
            logger.error("Database 'prathmesh' not found")
            raise
        except Table.DoesNotExist:
            logger.error(f"Table '{model_name}' not found in database")
            raise
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def ensure_relationships(self):
        """Ensure required relationships exist in Enrollments table"""
        try:
            with transaction.atomic():
                database = Database.objects.get(name="prathmesh")
                enrollments_table = Table.objects.get(database=database, name="Enrollments")
                courses_table = Table.objects.get(database=database, name="Courses")
                users_table = Table.objects.get(database=database, name="Users")

                # Check/Create course relationship
                course_field = enrollments_table.field_set.filter(
                    type='link_row',
                    link_row_table=courses_table
                ).first()
                if not course_field:
                    course_field = Field.objects.create(
                        table=enrollments_table,
                        name="course",
                        type="link_row",
                        link_row_table=courses_table,
                        order=0
                    )
                    logger.info(f"Created course link in Enrollments table (ID: {course_field.id})")

                # Check/Create user relationship
                user_field = enrollments_table.field_set.filter(
                    type='link_row',
                    link_row_table=users_table
                ).first()
                if not user_field:
                    user_field = Field.objects.create(
                        table=enrollments_table,
                        name="user",
                        type="link_row",
                        link_row_table=users_table,
                        order=1
                    )
                    logger.info(f"Created user link in Enrollments table (ID: {user_field.id})")

                return (
                    f'field_{course_field.id}',
                    f'field_{user_field.id}'
                )
        except Exception as e:
            logger.error(f"Error ensuring relationships: {str(e)}")
            return None, None

    def get_relation_field_id(self, table_name, target_table):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name=table_name)

            link_fields = table.field_set.filter(type='link_row')

            # First try exact matches where link_row_table is target_table
            for field in link_fields:
                if field.link_row_table.name == target_table:
                    return f'field_{field.id}'

            # Fallback: try common field names based on target table
            common_names = {
                "Courses": ['course', 'parent_course', 'related_course', 'course_link'],
                "Users": ['user', 'student', 'learner', 'participant']
            }.get(target_table, [])

            for name in common_names:
                try:
                    field = table.field_set.get(name=name, type='link_row')
                    if field.link_row_table.name == target_table:
                        return f'field_{field.id}'
                except Exception:
                    continue

            # If not found, try to create the relationship
            if target_table == "Courses":
                return self.ensure_relationships()[0]
            elif target_table == "Users":
                return self.ensure_relationships()[1]

            logger.error(f"No link_row field found in {table_name} linking to {target_table}")
            return None

        except Exception as e:
            logger.error(f"Error finding relation field in {table_name}: {str(e)}")
            return None

    def get_enrollment_data(self, enrollment):
        try:
            field_objects = enrollment.get_field_objects()
            enrollment_data = {
                'id': enrollment.id,
                'order': str(enrollment.order) if hasattr(enrollment, 'order') else None,
                'created_on': enrollment.created_on.isoformat() if enrollment.created_on else None,
                'updated_on': enrollment.updated_on.isoformat() if enrollment.updated_on else None
            }

            for field_object in field_objects:
                field_name = field_object['field'].name
                try:
                    field_value = getattr(enrollment, f'field_{field_object["field"].id}')
                    enrollment_data[field_name] = self.convert_field_value(
                        field_value,
                        field_object['type'].type
                    )
                except Exception as e:
                    logger.warning(f"Couldn't get field {field_name} value: {str(e)}")
                    enrollment_data[field_name] = None

            return enrollment_data
        except Exception as e:
            logger.error(f"Error formatting enrollment data: {str(e)}")
            raise

    def convert_field_value(self, value, field_type):
        if value is None:
            return None

        if field_type == 'number':
            return float(value)
        elif field_type == 'boolean':
            return bool(value)
        elif field_type in ['date', 'last_modified', 'created_on']:
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        elif field_type == 'link_row':
            if hasattr(value, 'all'):
                return [{'id': obj.id, 'value': str(obj)} for obj in value.all()]
            elif hasattr(value, 'id'):
                return {'id': value.id, 'value': str(value)}
            return None
        else:
            return value

    def get(self, request, enrollment_id=None):
        try:
            model, _ = self.get_model_and_table()

            if enrollment_id:
                enrollment = model.objects.get(id=enrollment_id)
                enrollment_data = self.get_enrollment_data(enrollment)
                return Response({"status": "success", "enrollment": enrollment_data})

            # Filter by course if course_id provided in query params
            course_id = request.query_params.get('course_id')
            user_id = request.query_params.get('user_id')

            filters = {}
            if course_id:
                course_field_id = self.get_relation_field_id("Enrollments", "Courses")
                if course_field_id:
                    filters[course_field_id] = course_id
                else:
                    return Response({
                        "error": "Course relationship not found in Enrollments table",
                        "solution": "Please ensure Enrollments table has a link to Courses table"
                    }, status=400)

            if user_id:
                user_field_id = self.get_relation_field_id("Enrollments", "Users")
                if user_field_id:
                    filters[user_field_id] = user_id
                else:
                    return Response({
                        "error": "User relationship not found in Enrollments table",
                        "solution": "Please ensure Enrollments table has a link to Users table"
                    }, status=400)

            enrollments = model.objects.filter(**filters) if filters else model.objects.all()

            return Response({
                "status": "success",
                "count": enrollments.count(),
                "enrollments": [self.get_enrollment_data(enrollment) for enrollment in enrollments]
            })
        except model.DoesNotExist:
            return Response({"error": "Enrollment not found"}, status=404)
        except Exception as e:
            logger.error(f"Error in EnrollmentsView GET: {str(e)}")
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        try:
            model, table = self.get_model_and_table()
            data = request.data

            # Ensure required fields exist or create them
            course_field_id, user_field_id = self.ensure_relationships()

            if not course_field_id or not user_field_id:
                return Response({
                    "error": "Missing required relationships in Enrollments table",
                    "solution": "Please ensure Enrollments table has links to both Courses and Users"
                }, status=400)

            # Check for required data
            if 'course' not in data or 'user' not in data:
                return Response({"error": "Both course and user IDs are required"}, status=400)

            # Check for existing enrollment
            existing = model.objects.filter(
                **{course_field_id: data['course'], user_field_id: data['user']}
            ).exists()
            if existing:
                return Response({"error": "User already enrolled in this course"}, status=400)

            field_objects = {fo['field'].name: fo for fo in table.get_field_objects()}
            enrollment_data = {
                course_field_id: data['course'],
                user_field_id: data['user']
            }

            for field_name, value in data.items():
                if field_name in field_objects and field_name not in ['course', 'user']:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type
                    enrollment_data[f'field_{field_id}'] = self.convert_field_value(value, field_type)

            enrollment = model.objects.create(**enrollment_data)
            return Response({
                "status": "success",
                "message": "Enrollment created successfully",
                "enrollment": self.get_enrollment_data(enrollment)
            }, status=201)
        except Exception as e:
            logger.error(f"Error creating enrollment: {str(e)}")
            return Response({"error": str(e)}, status=400)

    def put(self, request, enrollment_id):
        try:
            model, table = self.get_model_and_table()
            enrollment = model.objects.get(id=enrollment_id)
            data = request.data

            field_objects = {fo['field'].name: fo for fo in table.get_field_objects()}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type
                    setattr(enrollment, f'field_{field_id}', self.convert_field_value(value, field_type))

            enrollment.save()
            return Response({
                "status": "success",
                "message": "Enrollment updated successfully",
                "enrollment": self.get_enrollment_data(enrollment)
            })
        except model.DoesNotExist:
            return Response({"error": "Enrollment not found"}, status=404)
        except Exception as e:
            logger.error(f"Error updating enrollment: {str(e)}")
            return Response({"error": str(e)}, status=400)

    def delete(self, request, enrollment_id):
        try:
            model, _ = self.get_model_and_table()
            enrollment = model.objects.get(id=enrollment_id)
            enrollment.delete()
            return Response({
                "status": "success",
                "message": "Enrollment deleted successfully"
            })
        except model.DoesNotExist:
            return Response({"error": "Enrollment not found"}, status=404)
        except Exception as e:
            logger.error(f"Error deleting enrollment: {str(e)}")
            return Response({"error": str(e)}, status=400)


class ProgressView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Progress"):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def get_relation_field_id(self, table_name, target_table):
        try:
            database = Database.objects.get(name="prathmesh")
            table = Table.objects.get(database=database, name=table_name)

            link_fields = table.field_set.filter(type='link_row')

            # First try exact matches where link_row_table is target_table
            for field in link_fields:
                if field.link_row_table.name == target_table:
                    return f'field_{field.id}'

            # Fallback: try common field names based on target table
            common_names = {
                "Courses": ['course', 'parent_course', 'related_course'],
                "Users": ['user', 'student', 'learner'],
                "Lessons": ['lesson', 'module', 'content']
            }.get(target_table, [])

            for name in common_names:
                try:
                    field = table.field_set.get(name=name, type='link_row')
                    if field.link_row_table.name == target_table:
                        return f'field_{field.id}'
                except Exception:
                    continue

            logger.error(f"No link_row field found in {table_name} linking to {target_table}")
            return None

        except Exception as e:
            logger.error(f"Error finding relation field in {table_name}: {str(e)}")
            return None

    def get_progress_data(self, progress):
        try:
            field_objects = progress.get_field_objects()
            progress_data = {
                'id': progress.id,
                'order': str(progress.order) if hasattr(progress, 'order') else None,
                'created_on': progress.created_on.isoformat() if progress.created_on else None,
                'updated_on': progress.updated_on.isoformat() if progress.updated_on else None
            }

            for field_object in field_objects:
                field_name = field_object['field'].name
                try:
                    field_value = getattr(progress, f'field_{field_object["field"].id}')
                    progress_data[field_name] = self.convert_field_value(
                        field_value,
                        field_object['type'].type
                    )
                except Exception as e:
                    logger.warning(f"Couldn't get field {field_name} value: {str(e)}")
                    progress_data[field_name] = None

            return progress_data
        except Exception as e:
            logger.error(f"Error formatting progress data: {str(e)}")
            raise

    def convert_field_value(self, value, field_type):
        if value is None:
            return None

        if field_type == 'number':
            return float(value)
        elif field_type == 'boolean':
            return bool(value)
        elif field_type in ['date', 'last_modified', 'created_on']:
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        elif field_type == 'link_row':
            if hasattr(value, 'all'):
                return [{'id': obj.id, 'value': str(obj)} for obj in value.all()]
            elif hasattr(value, 'id'):
                return {'id': value.id, 'value': str(value)}
            return None
        else:
            return value

    def get(self, request, progress_id=None):
        try:
            model, _ = self.get_model_and_table()

            if progress_id:
                progress = model.objects.get(id=progress_id)
                progress_data = self.get_progress_data(progress)
                return Response({"status": "success", "progress": progress_data})

            # Filter by course, user, or lesson if provided in query params
            course_id = request.query_params.get('course_id')
            user_id = request.query_params.get('user_id')
            lesson_id = request.query_params.get('lesson_id')

            filters = {}
            if course_id:
                course_field_id = self.get_relation_field_id("Progress", "Courses")
                if course_field_id:
                    filters[course_field_id] = course_id
            if user_id:
                user_field_id = self.get_relation_field_id("Progress", "Users")
                if user_field_id:
                    filters[user_field_id] = user_id
            if lesson_id:
                lesson_field_id = self.get_relation_field_id("Progress", "Lessons")
                if lesson_field_id:
                    filters[lesson_field_id] = lesson_id

            progress_records = model.objects.filter(**filters) if filters else model.objects.all()

            # Calculate completion stats if course_id and user_id are provided
            if course_id and user_id:
                lesson_model, _ = self.get_model_and_table("Lessons")
                lesson_course_field_id = self.get_relation_field_id("Lessons", "Courses")

                if lesson_course_field_id:
                    total_lessons = lesson_model.objects.filter(**{lesson_course_field_id: course_id}).count()
                    completed_lessons = progress_records.filter(field_completed=True).count()

                    return Response({
                        "status": "success",
                        "count": progress_records.count(),
                        "progress": [self.get_progress_data(record) for record in progress_records],
                        "stats": {
                            "total_lessons": total_lessons,
                            "completed_lessons": completed_lessons,
                            "completion_percentage": round(
                                (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0, 2)
                        }
                    })

            return Response({
                "status": "success",
                "count": progress_records.count(),
                "progress": [self.get_progress_data(record) for record in progress_records]
            })
        except model.DoesNotExist:
            return Response({"error": "Progress record not found"}, status=404)
        except Exception as e:
            logger.error(f"Error in ProgressView GET: {str(e)}")
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        try:
            model, table = self.get_model_and_table()
            data = request.data

            # Ensure required fields exist
            course_field_id = self.get_relation_field_id("Progress", "Courses")
            user_field_id = self.get_relation_field_id("Progress", "Users")
            lesson_field_id = self.get_relation_field_id("Progress", "Lessons")

            if not all([course_field_id, user_field_id, lesson_field_id]):
                return Response({
                    "error": "Missing required relationships in Progress table",
                    "solution": "Please ensure Progress table has links to Courses, Users, and Lessons"
                }, status=400)

            # Check for required data
            required_fields = ['course', 'user', 'lesson']
            if not all(field in data for field in required_fields):
                return Response({"error": f"Required fields: {', '.join(required_fields)}"}, status=400)

            # Verify lesson belongs to course
            lesson_model, _ = self.get_model_and_table("Lessons")
            lesson_course_field_id = self.get_relation_field_id("Lessons", "Courses")

            if lesson_course_field_id:
                try:
                    lesson = lesson_model.objects.get(id=data['lesson'])
                    if getattr(lesson, lesson_course_field_id) != data['course']:
                        return Response({"error": "Lesson does not belong to specified course"}, status=400)
                except lesson_model.DoesNotExist:
                    return Response({"error": "Lesson not found"}, status=404)

            field_objects = {fo['field'].name: fo for fo in table.get_field_objects()}
            progress_data = {
                course_field_id: data['course'],
                user_field_id: data['user'],
                lesson_field_id: data['lesson'],
                'field_completed': data.get('completed', False),
                'field_last_accessed': datetime.now().isoformat()
            }

            for field_name, value in data.items():
                if field_name in field_objects and field_name not in required_fields:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type
                    progress_data[f'field_{field_id}'] = self.convert_field_value(value, field_type)

            progress = model.objects.create(**progress_data)
            return Response({
                "status": "success",
                "message": "Progress created successfully",
                "progress": self.get_progress_data(progress)
            }, status=201)
        except Exception as e:
            logger.error(f"Error creating progress: {str(e)}")
            return Response({"error": str(e)}, status=400)

    def put(self, request, progress_id):
        try:
            model, table = self.get_model_and_table()
            progress = model.objects.get(id=progress_id)
            data = request.data

            field_objects = {fo['field'].name: fo for fo in table.get_field_objects()}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type
                    setattr(progress, f'field_{field_id}', self.convert_field_value(value, field_type))

            if 'completed' in data:
                progress.field_completed = data['completed']
            progress.field_last_accessed = datetime.now().isoformat()

            progress.save()
            return Response({
                "status": "success",
                "message": "Progress updated successfully",
                "progress": self.get_progress_data(progress)
            })
        except model.DoesNotExist:
            return Response({"error": "Progress record not found"}, status=404)
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            return Response({"error": str(e)}, status=400)

    def delete(self, request, progress_id):
        try:
            model, _ = self.get_model_and_table()
            progress = model.objects.get(id=progress_id)
            progress.delete()
            return Response({
                "status": "success",
                "message": "Progress record deleted successfully"
            })
        except model.DoesNotExist:
            return Response({"error": "Progress record not found"}, status=404)
        except Exception as e:
            logger.error(f"Error deleting progress: {str(e)}")
            return Response({"error": str(e)}, status=400)
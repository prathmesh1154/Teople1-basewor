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
import traceback
from django.core.cache import cache


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
            database = Database.objects.get(name="Teople")
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
            database = Database.objects.get(name="Teople")
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
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
import traceback


@method_decorator(csrf_exempt, name='dispatch')
class UserRegisterView(APIView):
    permission_classes = (AllowAny,)

    def get_model(self):
        """Get the Users model from Baserow with dynamic field mapping"""
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name="Users")
            model = table.get_model()

            # Dynamically map field names to their IDs
            field_mapping = {}
            for field_obj in model.get_field_objects():
                field_name = field_obj['field'].name.lower().replace(' ', '_')
                field_mapping[field_name] = f'field_{field_obj["field"].id}'

            return model, field_mapping

        except Exception as e:
            logger.error(f"Error getting Users model: {str(e)}\n{traceback.format_exc()}")
            raise Exception("Failed to initialize user model")

    def post(self, request):
        """Handle user registration"""
        try:
            model, field_mapping = self.get_model()
            data = request.data

            # Validate required fields
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return Response({
                        "status": "error",
                        "message": f"{field} is required"
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Check if required fields exist in mapping
            missing_fields = [f for f in required_fields if f not in field_mapping]
            if missing_fields:
                return Response({
                    "status": "error",
                    "message": f"Missing field mappings for: {', '.join(missing_fields)}",
                    "available_fields": list(field_mapping.keys())
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Check for existing user
            if model.objects.filter(**{field_mapping['username']: data['username']}).exists():
                return Response({
                    "status": "error",
                    "message": "Username already exists"
                }, status=status.HTTP_409_CONFLICT)

            if model.objects.filter(**{field_mapping['email']: data['email']}).exists():
                return Response({
                    "status": "error",
                    "message": "Email already exists"
                }, status=status.HTTP_409_CONFLICT)

            # Prepare user data (excluding many-to-many fields)
            user_data = {
                field_mapping['username']: data['username'],
                field_mapping['email']: data['email'],
                field_mapping['password']: make_password(data['password']),
            }

            # Add optional fields if they exist in mapping and data
            optional_fields = ['first_name', 'last_name', 'is_active']
            for field in optional_fields:
                if field in field_mapping:
                    if field == 'is_active':
                        user_data[field_mapping[field]] = True
                    elif field in data:
                        user_data[field_mapping[field]] = data[field]

            # Create user without M2M fields first
            user = model.objects.create(**user_data)

            # Handle many-to-many fields (like roles) separately
            if 'roles' in field_mapping:
                try:
                    roles_field = getattr(user, field_mapping['roles'])
                    if isinstance(roles_field, list):  # For multiple select fields
                        user_data[field_mapping['roles']] = ["user"]
                        user.save()
                    else:  # For proper many-to-many relationships
                        roles_field.set(["user"])
                except Exception as e:
                    logger.error(f"Error setting roles: {str(e)}")
                    # Continue without roles if there's an error

            # Prepare response data
            response_data = {
                "id": user.id,
                "username": getattr(user, field_mapping['username']),
                "email": getattr(user, field_mapping['email'])
            }

            # Add roles to response if they exist
            if 'roles' in field_mapping:
                try:
                    roles = getattr(user, field_mapping['roles'])
                    if hasattr(roles, 'all'):  # If it's a manager
                        response_data['roles'] = [role.value for role in roles.all() if hasattr(role, 'value')]
                    elif isinstance(roles, list):  # If it's already a list
                        response_data['roles'] = roles
                except Exception as e:
                    logger.error(f"Error getting roles for response: {str(e)}")

            return Response({
                "status": "success",
                "message": "User registered successfully",
                "user": response_data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Registration error: {str(e)}\n{traceback.format_exc()}")
            return Response({
                "status": "error",
                "message": "Registration failed",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    permission_classes = (AllowAny,)

    def get_model(self):
        """Get the Users model from Baserow with dynamic field mapping"""
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name="Users")
            model = table.get_model()

            # Dynamically map field names to their IDs
            field_mapping = {}
            for field_obj in model.get_field_objects():
                field_name = field_obj['field'].name.lower().replace(' ', '_')
                field_mapping[field_name] = f'field_{field_obj["field"].id}'

            return model, field_mapping

        except Exception as e:
            logger.error(f"Error getting Users model: {str(e)}\n{traceback.format_exc()}")
            raise Exception("Failed to initialize user model")

    def post(self, request):
        """Handle user login"""
        try:
            model, field_mapping = self.get_model()
            data = request.data

            if not data.get('username') or not data.get('password'):
                return Response({
                    "status": "error",
                    "message": "Username and password are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Find user by username
            user = model.objects.filter(**{field_mapping['username']: data['username']}).first()
            if not user:
                return Response({
                    "status": "error",
                    "message": "Invalid credentials"
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Verify password
            if not check_password(data['password'], getattr(user, field_mapping['password'])):
                return Response({
                    "status": "error",
                    "message": "Invalid credentials"
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Check if account is active
            if 'is_active' in field_mapping and not getattr(user, field_mapping['is_active']):
                return Response({
                    "status": "error",
                    "message": "Account is inactive"
                }, status=status.HTTP_403_FORBIDDEN)

            # Update last login if field exists
            if 'last_login' in field_mapping:
                setattr(user, field_mapping['last_login'], datetime.now())
                user.save()

            # Create session
            request.session['user_id'] = user.id
            request.session.set_expiry(86400)  # 1 day expiration

            # Prepare response data
            response_data = {
                "id": user.id,
                "username": getattr(user, field_mapping['username']),
                "email": getattr(user, field_mapping['email'])
            }

            # Add roles if field exists
            if 'roles' in field_mapping:
                try:
                    roles = getattr(user, field_mapping['roles'])
                    if hasattr(roles, 'all'):  # If it's a manager
                        response_data['roles'] = [role.value for role in roles.all() if hasattr(role, 'value')]
                    elif isinstance(roles, list):  # If it's already a list
                        response_data['roles'] = roles
                except Exception as e:
                    logger.error(f"Error getting roles for login response: {str(e)}")

            return Response({
                "status": "success",
                "message": "Login successful",
                "user": response_data
            })

        except Exception as e:
            logger.error(f"Login error: {str(e)}\n{traceback.format_exc()}")
            return Response({
                "status": "error",
                "message": "Login failed",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class UserLogoutView(APIView):
    def post(self, request):
        """Handle user logout"""
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
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def convert_field_value(self, value, field_type):
        """
        Enhanced field value conversion that properly handles all Baserow field types
        including select options and link rows.
        """
        if value is None:
            return None

        if field_type == 'number':
            return float(value) if value is not None else None
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
        elif field_type == 'single_select':
            if value and hasattr(value, 'value'):
                return {
                    'id': value.id,
                    'value': value.value,
                    'color': value.color
                }
            return None
        elif field_type == 'multiple_select':
            if isinstance(value, list):
                return [{
                    'id': v.id,
                    'value': v.value,
                    'color': v.color
                } for v in value]
            return []
        else:
            return str(value) if value else None

    def get_course_data(self, course):
        """
        Serializes a course model instance to a dictionary with proper field handling
        """
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
            raise ValueError(f"Error serializing course: {str(e)}")

    def get(self, request, course_id=None):
        """
        Handle GET requests for single or multiple courses
        """
        try:
            model, _ = self.get_model_and_table()

            if course_id:
                course = model.objects.get(id=course_id)
                return Response({
                    "status": "success",
                    "course": self.get_course_data(course)
                })

            courses = model.objects.all()
            return Response({
                "status": "success",
                "count": courses.count(),
                "courses": [self.get_course_data(course) for course in courses]
            })
        except ObjectDoesNotExist:
            return Response({
                "status": "error",
                "message": "Course not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in CoursesView GET: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Handle course creation
        """
        try:
            model, table = self.get_model_and_table()
            data = request.data

            # Validate required fields
            if not data.get('title'):
                return Response({
                    "status": "error",
                    "message": "Title is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Prepare field mapping
            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
            course_data = {}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    # Handle special field types
                    if field_type == 'single_select' and isinstance(value, dict):
                        course_data[f'field_{field_id}'] = value.get('id')
                    elif field_type == 'multiple_select' and isinstance(value, list):
                        course_data[f'field_{field_id}'] = [v.get('id') for v in value]
                    else:
                        course_data[f'field_{field_id}'] = value

            # Create the course
            course = model.objects.create(**course_data)
            return Response({
                "status": "success",
                "message": "Course created successfully",
                "course": self.get_course_data(course)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, course_id):
        """
        Handle course updates
        """
        try:
            model, table = self.get_model_and_table()
            course = model.objects.get(id=course_id)
            data = request.data

            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    # Handle special field types
                    if field_type == 'single_select' and isinstance(value, dict):
                        setattr(course, f'field_{field_id}', value.get('id'))
                    elif field_type == 'multiple_select' and isinstance(value, list):
                        getattr(course, f'field_{field_id}').set([v.get('id') for v in value])
                    else:
                        setattr(course, f'field_{field_id}', value)

            course.save()
            return Response({
                "status": "success",
                "message": "Course updated successfully",
                "course": self.get_course_data(course)
            })

        except ObjectDoesNotExist:
            return Response({
                "status": "error",
                "message": "Course not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id):
        """
        Handle course deletion
        """
        try:
            model, _ = self.get_model_and_table()
            course = model.objects.get(id=course_id)
            course.delete()
            return Response({
                "status": "success",
                "message": "Course deleted successfully"
            })
        except ObjectDoesNotExist:
            return Response({
                "status": "error",
                "message": "Course not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting course: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LessonsView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Lessons"):
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def get_relation_field_id(self, table_name, target_table="Lessons"):
        try:
            database = Database.objects.get(name="Teople")
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
        except Exception as e:
            if 'model' in locals() and hasattr(e, 'DoesNotExist') and isinstance(e, model.DoesNotExist):
                return Response({"error": "Lesson not found"}, status=404)
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
        except Exception as e:
            if 'model' in locals() and hasattr(e, 'DoesNotExist') and isinstance(e, model.DoesNotExist):
                return Response({"error": "Lesson not found"}, status=404)
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
        except Exception as e:
            if 'model' in locals() and hasattr(e, 'DoesNotExist') and isinstance(e, model.DoesNotExist):
                return Response({"error": "Lesson not found"}, status=404)
            logger.error(f"Error deleting lesson: {str(e)}")
            return Response({"error": str(e)}, status=400)


class EnrollmentsView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Enrollments"):
        """Get the Baserow model and table with proper error handling"""
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Database.DoesNotExist:
            raise Exception("Database 'Teople' not found. Please create it in Baserow first.")
        except Table.DoesNotExist:
            raise Exception(f"Table '{model_name}' not found in database. Please create it.")
        except Exception as e:
            logger.error(f"Model initialization failed: {str(e)}\n{traceback.format_exc()}")
            raise Exception(f"Failed to initialize model: {str(e)}")

    def ensure_required_relationships(self):
        """Ensure Enrollments table has required links to Courses and Users"""
        try:
            with transaction.atomic():
                database = Database.objects.get(name="Teople")
                enrollments_table = Table.objects.get(database=database, name="Enrollments")
                courses_table = Table.objects.get(database=database, name="Courses")
                users_table = Table.objects.get(database=database, name="Users")

                required_fields = {
                    'course': courses_table,
                    'user': users_table
                }

                field_ids = {}

                for field_name, target_table in required_fields.items():
                    # Get all fields and filter for link_row type
                    all_fields = enrollments_table.field_set.all()
                    link_fields = [f for f in all_fields if hasattr(f, 'linkrowfield')]

                    # Find matching field
                    field = next(
                        (f for f in link_fields
                         if f.name == field_name and
                         f.linkrowfield.link_row_table_id == target_table.id),
                        None
                    )

                    if not field:
                        # Create new link_row field
                        field = Field.objects.create(
                            table=enrollments_table,
                            name=field_name,
                            type="link_row",
                            link_row_table=target_table,
                            order=len(all_fields)
                        )
                        logger.info(f"Created {field_name} link in Enrollments table (ID: {field.id})")

                    field_ids[field_name] = f'field_{field.id}'

                return field_ids

        except Exception as e:
            logger.error(f"Error ensuring required relationships: {str(e)}\n{traceback.format_exc()}")
            raise Exception(f"Failed to establish required relationships: {str(e)}")

    def get_relation_field_id(self, table_name, target_table):
        """Find the field ID for a relationship between tables"""
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name=table_name)

            # Get all fields and filter for link_row type
            all_fields = table.field_set.all()
            link_fields = [f for f in all_fields if hasattr(f, 'linkrowfield')]

            # First try exact matches where link_row_table is target_table
            for field in link_fields:
                if field.linkrowfield.link_row_table.name == target_table:
                    return f'field_{field.id}'

            # Fallback to common field names
            common_names = {
                "Courses": ['course', 'parent_course', 'related_course'],
                "Users": ['user', 'student', 'learner']
            }.get(target_table, [])

            for name in common_names:
                matching_fields = [f for f in link_fields if f.name == name]
                if matching_fields:
                    field = matching_fields[0]
                    if field.linkrowfield.link_row_table.name == target_table:
                        return f'field_{field.id}'

            logger.error(f"No link_row field found in {table_name} linking to {target_table}")
            return None

        except Exception as e:
            logger.error(f"Error finding relation field in {table_name}: {str(e)}\n{traceback.format_exc()}")
            return None

    def serialize_field_value(self, value, field_type):
        """Properly serialize all Baserow field types to JSON"""
        try:
            if value is None:
                return None

            # Handle each field type explicitly
            if field_type == 'number':
                return float(value) if value is not None else None
            elif field_type == 'boolean':
                return bool(value)
            elif field_type in ['date', 'last_modified', 'created_on']:
                return value.isoformat() if hasattr(value, 'isoformat') else str(value)
            elif field_type == 'link_row':
                if hasattr(value, 'all'):  # Many-to-many case
                    return [{'id': obj.id, 'value': str(obj)} for obj in value.all()]
                elif hasattr(value, 'id'):  # Foreign key case
                    return {'id': value.id, 'value': str(value)}
                return None
            elif field_type == 'single_select':
                return {
                    'id': value.id,
                    'value': value.value,
                    'color': value.color
                } if value else None
            elif field_type == 'multiple_select':
                return [{
                    'id': v.id,
                    'value': v.value,
                    'color': v.color
                } for v in value] if value else []
            else:  # Default case for text and other fields
                return str(value)
        except Exception as e:
            logger.error(f"Failed to serialize {field_type} field: {str(e)}")
            return None

    def get_enrollment_data(self, enrollment):
        """Convert an enrollment model instance to a serializable dictionary"""
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
                    enrollment_data[field_name] = self.serialize_field_value(
                        field_value,
                        field_object['type'].type
                    )
                except Exception as e:
                    logger.warning(f"Field '{field_name}' access error: {str(e)}")
                    enrollment_data[field_name] = None

            return enrollment_data
        except Exception as e:
            logger.error(f"Enrollment serialization failed: {str(e)}\n{traceback.format_exc()}")
            raise Exception(f"Failed to serialize enrollment data: {str(e)}")

    def get(self, request, enrollment_id=None):
        """Handle GET requests for enrollments"""
        try:
            model, _ = self.get_model_and_table()

            if enrollment_id:
                enrollment = model.objects.get(id=enrollment_id)
                return Response({
                    "status": "success",
                    "enrollment": self.get_enrollment_data(enrollment)
                })

            # Ensure required relationships exist
            required_fields = self.ensure_required_relationships()
            if not required_fields:
                return Response({
                    "status": "error",
                    "message": "Missing required relationships in Enrollments table",
                    "solution": "Please ensure Enrollments table has links to Courses and Users"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Build filters
            filters = {}
            course_id = request.query_params.get('course_id')
            user_id = request.query_params.get('user_id')

            if course_id:
                filters[required_fields['course']] = course_id
            if user_id:
                filters[required_fields['user']] = user_id

            enrollments = model.objects.filter(**filters) if filters else model.objects.all()

            return Response({
                "status": "success",
                "count": enrollments.count(),
                "enrollments": [self.get_enrollment_data(e) for e in enrollments]
            })

        except ObjectDoesNotExist:
            return Response({
                "status": "error",
                "message": f"Enrollment {enrollment_id} not found" if enrollment_id else "No enrollments found",
                "type": "not_found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e) or "Failed to fetch enrollments",
                "type": type(e).__name__,
                "details": traceback.format_exc().splitlines()[-1]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Handle enrollment creation"""
        try:
            model, table = self.get_model_and_table()
            data = request.data

            # Ensure required relationships exist
            required_fields = self.ensure_required_relationships()
            if not required_fields:
                return Response({
                    "status": "error",
                    "message": "Missing required relationships in Enrollments table",
                    "solution": "Please ensure Enrollments table has links to Courses and Users"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate required fields
            required_data_fields = ['course', 'user']
            if not all(field in data for field in required_data_fields):
                return Response({
                    "status": "error",
                    "message": f"Required fields: {', '.join(required_data_fields)}",
                    "type": "validation_error"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check for existing enrollment
            existing = model.objects.filter(
                **{required_fields['course']: data['course'],
                   required_fields['user']: data['user']}
            ).exists()
            if existing:
                return Response({
                    "status": "error",
                    "message": "User already enrolled in this course",
                    "type": "duplicate_entry"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Prepare data
            temp_instance = model()
            field_objects = {fo['field'].name: fo for fo in temp_instance.get_field_objects()}
            m2m_updates = {}
            enrollment_data = {}

            # Set course and user (these might be M2M in Baserow, handle carefully)
            for field_name in required_data_fields:
                field_obj = field_objects.get(field_name)
                if field_obj and field_obj['type'].type == "link_row":
                    # store for later set()
                    m2m_updates[f'field_{field_obj["field"].id}'] = [data[field_name]]
                else:
                    enrollment_data[required_fields[field_name]] = data[field_name]

            # Handle other fields
            for field_name, value in data.items():
                if field_name in field_objects and field_name not in required_data_fields:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    if field_type == "link_row":
                        m2m_updates[f'field_{field_id}'] = value if isinstance(value, list) else [value]
                    else:
                        enrollment_data[f'field_{field_id}'] = value

            # Save instance first
            enrollment = model.objects.create(**enrollment_data)

            # Now handle M2M updates
            for field_key, values in m2m_updates.items():
                getattr(enrollment, field_key).set(values)

            return Response({
                "status": "success",
                "message": "Enrollment created successfully",
                "enrollment": self.get_enrollment_data(enrollment)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e) or "Failed to create enrollment",
                "type": type(e).__name__
            }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, enrollment_id):
        """Handle enrollment updates"""
        try:
            model, table = self.get_model_and_table()
            enrollment = model.objects.get(id=enrollment_id)
            data = request.data

            field_objects = {fo['field'].name: fo for fo in enrollment.get_field_objects()}
            m2m_updates = {}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    if field_type == "link_row":  # M2M
                        m2m_updates[f'field_{field_id}'] = value if isinstance(value, list) else [value]
                    else:
                        setattr(enrollment, f'field_{field_id}', value)

            enrollment.save()

            # Now update M2M
            for field_key, values in m2m_updates.items():
                getattr(enrollment, field_key).set(values)

            return Response({
                "status": "success",
                "message": "Enrollment updated successfully",
                "enrollment": self.get_enrollment_data(enrollment)
            })

        except ObjectDoesNotExist:
            return Response({
                "status": "error",
                "message": "Enrollment not found",
                "type": "not_found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e) or "Failed to update enrollment",
                "type": type(e).__name__
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, enrollment_id):
        """Handle enrollment deletion"""
        try:
            model, _ = self.get_model_and_table()
            enrollment = model.objects.get(id=enrollment_id)
            enrollment.delete()
            return Response({
                "status": "success",
                "message": "Enrollment deleted successfully"
            })
        except ObjectDoesNotExist:
            return Response({
                "status": "error",
                "message": "Enrollment not found",
                "type": "not_found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e) or "Failed to delete enrollment",
                "type": type(e).__name__
            }, status=status.HTTP_400_BAD_REQUEST)

from django.db.models import Manager as BaseManager

class ProgressView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Progress"):
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def ensure_required_relationships(self):
        """Ensure Progress table has required links to Courses, Users, and Lessons"""
        try:
            with transaction.atomic():
                database = Database.objects.get(name="Teople")
                progress_table = Table.objects.get(database=database, name="Progress")
                courses_table = Table.objects.get(database=database, name="Courses")
                users_table = Table.objects.get(database=database, name="Users")
                lessons_table = Table.objects.get(database=database, name="Lessons")

                required_fields = {
                    'course': courses_table,
                    'user': users_table,
                    'lesson': lessons_table
                }

                field_ids = {}

                for field_name, target_table in required_fields.items():
                    all_fields = progress_table.field_set.all()
                    link_fields = [f for f in all_fields if hasattr(f, 'linkrowfield')]

                    field = next(
                        (f for f in link_fields
                         if f.name == field_name and
                         f.linkrowfield.link_row_table_id == target_table.id),
                        None
                    )

                    if not field:
                        field = Field.objects.create(
                            table=progress_table,
                            name=field_name,
                            type="link_row",
                            link_row_table=target_table,
                            order=len(all_fields)
                        )
                        logger.info(f"Created {field_name} link in Progress table (ID: {field.id})")

                    field_ids[field_name] = f'field_{field.id}'

                return field_ids

        except Exception as e:
            logger.error(f"Error ensuring required relationships: {str(e)}")
            raise

    def get_relation_field_id(self, table_name, target_table):
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name=table_name)

            all_fields = table.field_set.all()
            link_fields = [f for f in all_fields if hasattr(f, 'linkrowfield')]

            for field in link_fields:
                if field.linkrowfield.link_row_table.name == target_table:
                    return f'field_{field.id}'

            common_names = {
                "Courses": ['course', 'parent_course', 'related_course'],
                "Users": ['user', 'student', 'learner'],
                "Lessons": ['lesson', 'module', 'content']
            }.get(target_table, [])

            for name in common_names:
                matching_fields = [f for f in link_fields if f.name == name]
                if matching_fields:
                    field = matching_fields[0]
                    if field.linkrowfield.link_row_table.name == target_table:
                        return f'field_{field.id}'

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
                        field_object['type']
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

        if isinstance(value, BaseManager):
            return [{'id': obj.id, 'value': str(obj)} for obj in value.all()]

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

            required_fields = self.ensure_required_relationships()
            if not required_fields:
                return Response({
                    "error": "Missing required relationships in Progress table",
                    "solution": "Please ensure Progress table has links to Courses, Users, and Lessons"
                }, status=400)

            filters = {}
            course_id = request.query_params.get('course_id')
            user_id = request.query_params.get('user_id')
            lesson_id = request.query_params.get('lesson_id')

            if course_id:
                filters[required_fields['course']] = course_id
            if user_id:
                filters[required_fields['user']] = user_id
            if lesson_id:
                filters[required_fields['lesson']] = lesson_id

            progress_records = model.objects.filter(**filters) if filters else model.objects.all()

            return Response({
                "status": "success",
                "count": progress_records.count(),
                "progress": [self.get_progress_data(record) for record in progress_records]
            })
        except Exception as e:
            if 'model' in locals() and hasattr(e, 'DoesNotExist') and isinstance(e, model.DoesNotExist):
                return Response({"error": "Progress record not found"}, status=404)
            logger.error(f"Error in ProgressView GET: {str(e)}")
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        try:
            model, table = self.get_model_and_table()
            data = request.data

            required_fields = self.ensure_required_relationships()
            if not required_fields:
                return Response({
                    "error": "Missing required relationships in Progress table",
                    "solution": "Please ensure Progress table has links to Courses, Users, and Lessons"
                }, status=400)

            required_data_fields = ['course', 'user', 'lesson']
            if not all(field in data for field in required_data_fields):
                return Response({"error": f"Required fields: {', '.join(required_data_fields)}"}, status=400)

            # ✅ Create progress instance without unknown kwargs
            progress = model.objects.create()

            # ✅ Set M2M relations properly
            getattr(progress, required_fields['course']).set(data['course'])
            getattr(progress, required_fields['user']).set(data['user'])
            getattr(progress, required_fields['lesson']).set(data['lesson'])

            if 'completed' in data:
                # find actual field id for "completed"
                field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
                if 'completed' in field_objects:
                    field_id = field_objects['completed']['field'].id
                    setattr(progress, f'field_{field_id}', data['completed'])

            # handle extra optional fields
            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
            for field_name, value in data.items():
                if field_name in field_objects and field_name not in required_data_fields + ['completed']:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    setattr(progress, f'field_{field_id}', value)

            progress.save()

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

            # ✅ FIX: use model.get_field_objects()
            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    setattr(progress, f'field_{field_id}', value)

            progress.save()
            return Response({
                "status": "success",
                "message": "Progress updated successfully",
                "progress": self.get_progress_data(progress)
            })
        except Exception as e:
            if 'model' in locals() and hasattr(e, 'DoesNotExist') and isinstance(e, model.DoesNotExist):
                return Response({"error": "Progress record not found"}, status=404)
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
        except Exception as e:
            if 'model' in locals() and hasattr(e, 'DoesNotExist') and isinstance(e, model.DoesNotExist):
                return Response({"error": "Progress record not found"}, status=404)
            logger.error(f"Error deleting progress: {str(e)}")
            return Response({"error": str(e)}, status=400)


class QuizView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Quiz"):
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def ensure_required_relationships(self):
        """Ensure Quiz table has required links to Courses"""
        try:
            with transaction.atomic():
                database = Database.objects.get(name="Teople")
                quiz_table = Table.objects.get(database=database, name="Quiz")
                courses_table = Table.objects.get(database=database, name="Courses")

                # Check if course relationship exists
                all_fields = quiz_table.field_set.all()
                link_fields = [f for f in all_fields if hasattr(f, 'linkrowfield')]

                course_field = next(
                    (f for f in link_fields
                     if f.linkrowfield.link_row_table_id == courses_table.id),
                    None
                )

                if not course_field:
                    course_field = Field.objects.create(
                        table=quiz_table,
                        name="course",
                        type="link_row",
                        link_row_table=courses_table,
                        order=len(all_fields)
                    )
                    logger.info(f"Created course link in Quiz table (ID: {course_field.id})")

                return {
                    'course': f'field_{course_field.id}'
                }

        except Exception as e:
            logger.error(f"Error ensuring required relationships: {str(e)}")
            raise

    def get_quiz_data(self, quiz):
        try:
            field_objects = quiz.get_field_objects()
            quiz_data = {
                'id': quiz.id,
                'order': str(quiz.order) if hasattr(quiz, 'order') else None,
                'created_on': quiz.created_on.isoformat() if quiz.created_on else None,
                'updated_on': quiz.updated_on.isoformat() if quiz.updated_on else None
            }

            for field_object in field_objects:
                field_name = field_object['field'].name
                try:
                    field_value = getattr(quiz, f'field_{field_object["field"].id}')
                    quiz_data[field_name] = self.convert_field_value(
                        field_value,
                        field_object['type'].type
                    )
                except Exception as e:
                    logger.warning(f"Couldn't get field {field_name} value: {str(e)}")
                    quiz_data[field_name] = None

            return quiz_data
        except Exception as e:
            logger.error(f"Error formatting quiz data: {str(e)}")
            raise

    def convert_field_value(self, value, field_type):
        if value is None:
            return None

        if field_type == 'number':
            return float(value) if value is not None else None
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
        elif field_type == 'single_select':
            if value and hasattr(value, 'value'):
                return {
                    'id': value.id,
                    'value': value.value,
                    'color': value.color
                }
            return None
        elif field_type == 'multiple_select':
            if isinstance(value, list):
                return [{
                    'id': v.id,
                    'value': v.value,
                    'color': v.color
                } for v in value]
            return []
        else:
            return str(value) if value else None

    def get(self, request, quiz_id=None):
        try:
            model, _ = self.get_model_and_table()

            if quiz_id:
                quiz = model.objects.get(id=quiz_id)
                return Response({
                    "status": "success",
                    "quiz": self.get_quiz_data(quiz)
                })

            # Apply course filter if provided
            course_id = request.query_params.get('course_id')
            quizzes = model.objects.all()

            if course_id:
                required_fields = self.ensure_required_relationships()
                if required_fields and 'course' in required_fields:
                    quizzes = quizzes.filter(**{required_fields['course']: course_id})

            return Response({
                "status": "success",
                "count": quizzes.count(),
                "quizzes": [self.get_quiz_data(quiz) for quiz in quizzes]
            })
        except model.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Quiz not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in QuizView GET: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            model, table = self.get_model_and_table()
            data = request.data

            # # Validate required fields
            # if not data.get('title'):
            #     return Response({
            #         "status": "error",
            #         "message": "Title is required"
            #     }, status=status.HTTP_400_BAD_REQUEST)

            # Ensure course relationship exists
            required_fields = self.ensure_required_relationships()
            if not required_fields or 'course' not in required_fields:
                return Response({
                    "status": "error",
                    "message": "Quiz must be associated with a course"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Prepare field mapping
            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
            quiz_data = {}
            link_row_fields = {}  # Store link row fields to handle separately

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    if field_type == 'single_select' and isinstance(value, dict):
                        quiz_data[f'field_{field_id}'] = value.get('id')
                    elif field_type == 'multiple_select' and isinstance(value, list):
                        quiz_data[f'field_{field_id}'] = [v.get('id') for v in value]
                    elif field_type == 'link_row':
                        # Store link row fields to handle after creation
                        link_row_fields[f'field_{field_id}'] = value
                    else:
                        quiz_data[f'field_{field_id}'] = value

            # Create the quiz
            quiz = model.objects.create(**quiz_data)

            # Handle link_row fields using set() method
            for field_id, value in link_row_fields.items():
                if hasattr(quiz, field_id):
                    # Convert single value to list if needed
                    values_list = value if isinstance(value, list) else [value]
                    getattr(quiz, field_id).set(values_list)

            return Response({
                "status": "success",
                "message": "Quiz created successfully",
                "quiz": self.get_quiz_data(quiz)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating quiz: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, quiz_id):
        try:
            model, table = self.get_model_and_table()
            quiz = model.objects.get(id=quiz_id)
            data = request.data

            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
            link_row_fields = {}  # Store link row fields to handle separately

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    if field_type == 'single_select' and isinstance(value, dict):
                        setattr(quiz, f'field_{field_id}', value.get('id'))
                    elif field_type == 'multiple_select' and isinstance(value, list):
                        getattr(quiz, f'field_{field_id}').set([v.get('id') for v in value])
                    elif field_type == 'link_row':
                        # Store link row fields to handle after saving
                        link_row_fields[f'field_{field_id}'] = value
                    else:
                        setattr(quiz, f'field_{field_id}', value)

            quiz.save()

            # Handle link_row fields using set() method after saving
            for field_id, value in link_row_fields.items():
                if hasattr(quiz, field_id):
                    # Convert single value to list if needed
                    values_list = value if isinstance(value, list) else [value]
                    getattr(quiz, field_id).set(values_list)

            return Response({
                "status": "success",
                "message": "Quiz updated successfully",
                "quiz": self.get_quiz_data(quiz)
            })

        except model.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Quiz not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating quiz: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, quiz_id):
        try:
            model, _ = self.get_model_and_table()
            quiz = model.objects.get(id=quiz_id)
            quiz.delete()
            return Response({
                "status": "success",
                "message": "Quiz deleted successfully"
            })
        except model.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Quiz not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting quiz: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class QuestionsView(APIView):
    permission_classes = (AllowAny,)

    def get_model_and_table(self, model_name="Questions"):
        try:
            database = Database.objects.get(name="Teople")
            table = Table.objects.get(database=database, name=model_name)
            model = table.get_model()
            return model, table
        except Exception as e:
            logger.error(f"Error getting model and table for {model_name}: {str(e)}")
            raise

    def ensure_required_relationships(self):
        """Ensure Questions table has required links to Quiz"""
        try:
            with transaction.atomic():
                database = Database.objects.get(name="Teople")
                questions_table = Table.objects.get(database=database, name="Questions")
                quiz_table = Table.objects.get(database=database, name="Quiz")

                # Check if quiz relationship exists
                all_fields = questions_table.field_set.all()
                link_fields = [f for f in all_fields if hasattr(f, 'linkrowfield')]

                quiz_field = next(
                    (f for f in link_fields
                     if f.linkrowfield.link_row_table_id == quiz_table.id),
                    None
                )

                if not quiz_field:
                    quiz_field = Field.objects.create(
                        table=questions_table,
                        name="quiz",
                        type="link_row",
                        link_row_table=quiz_table,
                        order=len(all_fields)
                    )
                    logger.info(f"Created quiz link in Questions table (ID: {quiz_field.id})")

                return {
                    'quiz': f'field_{quiz_field.id}'
                }

        except Exception as e:
            logger.error(f"Error ensuring required relationships: {str(e)}")
            raise

    def get_question_data(self, question):
        try:
            field_objects = question.get_field_objects()
            question_data = {
                'id': question.id,
                'order': str(question.order) if hasattr(question, 'order') else None,
                'created_on': question.created_on.isoformat() if question.created_on else None,
                'updated_on': question.updated_on.isoformat() if question.updated_on else None
            }

            for field_object in field_objects:
                field_name = field_object['field'].name
                try:
                    field_value = getattr(question, f'field_{field_object["field"].id}')
                    question_data[field_name] = self.convert_field_value(
                        field_value,
                        field_object['type'].type
                    )
                except Exception as e:
                    logger.warning(f"Couldn't get field {field_name} value: {str(e)}")
                    question_data[field_name] = None

            return question_data
        except Exception as e:
            logger.error(f"Error formatting question data: {str(e)}")
            raise

    def convert_field_value(self, value, field_type):
        if value is None:
            return None

        if field_type == 'number':
            return float(value) if value is not None else None
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
        elif field_type == 'single_select':
            if value and hasattr(value, 'value'):
                return {
                    'id': value.id,
                    'value': value.value,
                    'color': value.color
                }
            return None
        elif field_type == 'multiple_select':
            if isinstance(value, list):
                return [{
                    'id': v.id,
                    'value': v.value,
                    'color': v.color
                } for v in value]
            return []
        else:
            return str(value) if value else None

    def get(self, request, question_id=None):
        try:
            model, _ = self.get_model_and_table()

            if question_id:
                question = model.objects.get(id=question_id)
                return Response({
                    "status": "success",
                    "question": self.get_question_data(question)
                })

            # Apply quiz filter if provided
            quiz_id = request.query_params.get('quiz_id')
            questions = model.objects.all()

            if quiz_id:
                required_fields = self.ensure_required_relationships()
                if required_fields and 'quiz' in required_fields:
                    questions = questions.filter(**{required_fields['quiz']: quiz_id})

            return Response({
                "status": "success",
                "count": questions.count(),
                "questions": [self.get_question_data(question) for question in questions]
            })
        except model.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Question not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in QuestionsView GET: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            model, table = self.get_model_and_table()
            data = request.data

            # Validate required fields
            if not data.get('question_text'):
                return Response({
                    "status": "error",
                    "message": "Question text is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Ensure quiz relationship exists
            required_fields = self.ensure_required_relationships()
            if not required_fields or 'quiz' not in required_fields:
                return Response({
                    "status": "error",
                    "message": "Question must be associated with a quiz"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Prepare field mapping
            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}
            question_data = {}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    if field_type == 'single_select' and isinstance(value, dict):
                        question_data[f'field_{field_id}'] = value.get('id')
                    elif field_type == 'multiple_select' and isinstance(value, list):
                        question_data[f'field_{field_id}'] = [v.get('id') for v in value]
                    elif field_type == 'link_row':
                        question_data[f'field_{field_id}'] = value  # Will be handled by set() later
                    else:
                        question_data[f'field_{field_id}'] = value

            # Create the question
            question = model.objects.create(**question_data)

            # Handle link_row fields separately
            for field_name, value in data.items():
                if field_name in field_objects and field_objects[field_name]['type'].type == 'link_row':
                    field_id = field_objects[field_name]['field'].id
                    getattr(question, f'field_{field_id}').set(value if isinstance(value, list) else [value])

            return Response({
                "status": "success",
                "message": "Question created successfully",
                "question": self.get_question_data(question)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating question: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, question_id):
        try:
            model, table = self.get_model_and_table()
            question = model.objects.get(id=question_id)
            data = request.data

            field_objects = {fo['field'].name: fo for fo in model.get_field_objects()}

            for field_name, value in data.items():
                if field_name in field_objects:
                    field_obj = field_objects[field_name]
                    field_id = field_obj['field'].id
                    field_type = field_obj['type'].type

                    if field_type == 'single_select' and isinstance(value, dict):
                        setattr(question, f'field_{field_id}', value.get('id'))
                    elif field_type == 'multiple_select' and isinstance(value, list):
                        getattr(question, f'field_{field_id}').set([v.get('id') for v in value])
                    elif field_type == 'link_row':
                        getattr(question, f'field_{field_id}').set(value if isinstance(value, list) else [value])
                    else:
                        setattr(question, f'field_{field_id}', value)

            question.save()
            return Response({
                "status": "success",
                "message": "Question updated successfully",
                "question": self.get_question_data(question)
            })

        except model.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Question not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating question: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, question_id):
        try:
            model, _ = self.get_model_and_table()
            question = model.objects.get(id=question_id)
            question.delete()
            return Response({
                "status": "success",
                "message": "Question deleted successfully"
            })
        except model.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Question not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting question: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
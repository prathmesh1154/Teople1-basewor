import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.models import Database
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
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
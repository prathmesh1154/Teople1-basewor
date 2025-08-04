from django.urls import re_path

from .views import StartingView ,TasksView ,CategoriesView

app_name = "teople1.api"

urlpatterns = [
    re_path(r"starting/$", StartingView.as_view(), name="starting"),
    re_path(r"tasks/$", TasksView.as_view(), name="tasks"),  # New endpoints
    re_path(r"tasks/(?P<task_id>\d+)/$", TasksView.as_view(), name="task_detail"),
    re_path(r"categories/$", CategoriesView.as_view(), name="categories"),
    re_path(r"categories/(?P<category_id>\d+)/$", CategoriesView.as_view(), name="category_detail"),
]

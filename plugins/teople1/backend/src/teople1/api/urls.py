from django.urls import re_path
from .views import (
    StartingView,
    TasksView,
    CategoriesView,
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    CoursesView,
    LessonsView,
    EnrollmentsView,
    ProgressView,
)

app_name = "teople1.api"

urlpatterns = [
    re_path(r"starting/$", StartingView.as_view(), name="starting"),

    re_path(r"tasks/$", TasksView.as_view(), name="tasks"),
    re_path(r"tasks/(?P<task_id>\d+)/$", TasksView.as_view(), name="task_detail"),

    re_path(r"categories/$", CategoriesView.as_view(), name="categories"),
    re_path(r"categories/(?P<category_id>\d+)/$", CategoriesView.as_view(), name="category_detail"),

    re_path(r"users/register/$", UserRegisterView.as_view(), name="user_register"),
    re_path(r"users/login/$", UserLoginView.as_view(), name="user_login"),
    re_path(r"users/logout/$", UserLogoutView.as_view(), name="user_logout"),

    # Courses endpoints
    re_path(r"courses/$", CoursesView.as_view(), name="courses"),
    re_path(r"courses/(?P<course_id>\d+)/$", CoursesView.as_view(), name="course_detail"),

    # Lessons endpoints nested under courses
    re_path(r"lessons/$", LessonsView.as_view(), name="course_lessons"),
    re_path(r"lessons/(?P<lesson_id>\d+)/$", LessonsView.as_view(), name="lesson_detail"),

    # Enrollments endpoints nested under courses
    re_path(r"enrollments/$", EnrollmentsView.as_view(), name="course_enrollments"),
    re_path(r"enrollments/(?P<enrollment_id>\d+)/$", EnrollmentsView.as_view(),
            name="enrollment_detail"),

    # Progress endpoints nested under courses
    re_path(r"progress/$", ProgressView.as_view(), name="course_progress"),
    re_path(r"progress/(?P<lesson_id>\d+)/$", ProgressView.as_view(),
            name="lesson_progress"),
]

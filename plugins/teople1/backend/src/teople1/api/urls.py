from django.urls import re_path
from .views import StartingView, TasksView, CategoriesView, UserRegisterView, UserLoginView, UserLogoutView, CourseView,LessonView,EnrollmentView,UserProgressView



app_name = "teople1.api"

urlpatterns = [
    re_path(r"starting/$", StartingView.as_view(), name="starting"),
    re_path(r"tasks/$", TasksView.as_view(), name="tasks"),  # New endpoints
    re_path(r"tasks/(?P<task_id>\d+)/$", TasksView.as_view(), name="task_detail"),
    re_path(r"categories/$", CategoriesView.as_view(), name="categories"),
    re_path(r"categories/(?P<category_id>\d+)/$", CategoriesView.as_view(), name="category_detail"),
    re_path(r"users/register/$", UserRegisterView.as_view(), name="user_register"),
    re_path(r"users/login/$", UserLoginView.as_view(), name="user_login"),
    re_path(r"users/logout/$", UserLogoutView.as_view(), name="user_logout"),
    re_path(r"courses/$", CourseView.as_view(), name="course_list"),
    re_path(r"courses/(?P<course_id>\d+)/$", CourseView.as_view(), name="course_detail"),

    # Lesson management
    re_path(r"lessons/$", LessonView.as_view(), name="lesson_list"),
    re_path(r"lessons/(?P<lesson_id>\d+)/$", LessonView.as_view(), name="lesson_detail"),
    re_path(r"courses/(?P<course_id>\d+)/lessons/$", LessonView.as_view(), name="course_lessons"),

    # Enrollment management
    re_path(r"courses/(?P<course_id>\d+)/enroll/$", EnrollmentView.as_view(), name="course_enroll"),

    # Progress tracking
    re_path(r"lessons/(?P<lesson_id>\d+)/complete/$", UserProgressView.as_view(), name="lesson_complete"),
]

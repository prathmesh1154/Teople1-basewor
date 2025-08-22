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
    QuizView,
    QuestionsView,
)

app_name = "teople1.api"

urlpatterns = [
    # Starting endpoint
    re_path(r"starting/$", StartingView.as_view(), name="starting"),

    # Tasks endpoints
    re_path(r"tasks/$", TasksView.as_view(), name="tasks"),
    re_path(r"tasks/(?P<task_id>\d+)/$", TasksView.as_view(), name="task_detail"),

    # Categories endpoints
    re_path(r"categories/$", CategoriesView.as_view(), name="categories"),
    re_path(r"categories/(?P<category_id>\d+)/$", CategoriesView.as_view(), name="category_detail"),

    # User authentication endpoints
    re_path(r"users/register/$", UserRegisterView.as_view(), name="user_register"),
    re_path(r"users/login/$", UserLoginView.as_view(), name="user_login"),
    re_path(r"users/logout/$", UserLogoutView.as_view(), name="user_logout"),

    # Courses endpoints
    re_path(r"courses/$", CoursesView.as_view(), name="courses"),
    re_path(r"courses/(?P<course_id>\d+)/$", CoursesView.as_view(), name="course_detail"),

    # Lessons endpoints
    re_path(r"lessons/$", LessonsView.as_view(), name="lessons"),
    re_path(r"lessons/(?P<lesson_id>\d+)/$", LessonsView.as_view(), name="lesson_detail"),

    # Enrollments endpoints
    re_path(r"enrollments/$", EnrollmentsView.as_view(), name="enrollments"),
    re_path(r"enrollments/(?P<enrollment_id>\d+)/$", EnrollmentsView.as_view(), name="enrollment_detail"),

    # Progress endpoints
    re_path(r"progress/$", ProgressView.as_view(), name="progress"),
    re_path(r"progress/(?P<progress_id>\d+)/$", ProgressView.as_view(), name="progress_detail"),

    # Quiz endpoints (new)
    re_path(r"quizzes/$", QuizView.as_view(), name="quizzes"),
    re_path(r"quizzes/(?P<quiz_id>\d+)/$", QuizView.as_view(), name="quiz_detail"),

    # Questions endpoints (new)
    re_path(r"questions/$", QuestionsView.as_view(), name="questions"),
    re_path(r"questions/(?P<question_id>\d+)/$", QuestionsView.as_view(), name="question_detail"),
]
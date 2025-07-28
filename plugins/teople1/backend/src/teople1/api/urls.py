from django.urls import re_path

from .views import StartingView ,LoginView

app_name = "teople1.api"

urlpatterns = [
    re_path(r"starting/$", StartingView.as_view(), name="starting"),
    re_path(r"custom-login/$", LoginView.as_view(), name="login"),
]

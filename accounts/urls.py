from django.urls import include, path

from accounts.views import SignUp

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", SignUp.as_view(), name="signup"),
]

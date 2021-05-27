from django.urls import include
from django.urls import path

from accounts.views import SignUpView

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path('accounts/signup/', SignUpView.as_view(), name='signup'),
]

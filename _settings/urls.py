from django.contrib import admin
from django.urls import include
from django.urls import path

urlpatterns = [
    path("", include("wb.urls")),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
]

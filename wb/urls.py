from django.urls import path

from wb import views

urlpatterns = [
    path(
        "",
        views.index,
    ),
]

from django.urls import path

from wb import views

urlpatterns = [
    path("", views.index, name="index"),
    path("stock/", views.stock, name="stock"),
    path("ordered/", views.ordered, name="ordered"),
    path("bought/", views.bought, name="bought"),
]

from django.urls import path

from wb import views

urlpatterns = [
    path("", views.index, name="index"),
    path("stock/", views.stock, name="stock"),
    path("ordered/", views.ordered, name="ordered"),
    path("bought/", views.bought, name="bought"),
    path("api/", views.api, name="api"),
    path("summary/", views.weekly_orders_summary, name="summary"),
    path("add/", views.add_to_cart, name="add"),
    path("cart/", views.cart, name="cart"),
]

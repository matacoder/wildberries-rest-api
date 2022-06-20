from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from wb import views

urlpatterns = [
    path("", views.index, name="index"),
    path("stock/", views.stock, name="stock"),
    path("marketplace/", views.marketplace, name="marketplace"),
    path("ordered/", views.ordered, name="ordered"),
    path("bought/", views.bought, name="bought"),
    path("api/", views.api, name="api"),
    path("summary/", views.weekly_orders_summary, name="summary"),
    path("add/", views.add_to_cart, name="add"),
    path("cart/", views.cart, name="cart"),
    path("update_discount/", views.update_discount, name="update_discount"),
]

urlpatterns += [
    path("api/v1/stock", views.api_stock, name="api_stock"),
    path("api/v1/marketplace", views.api_marketplace, name="api_marketplace"),
]

schema_view = get_schema_view(
    openapi.Info(
        title="WB.Matakov.com API",
        default_version="v1",
        description="Products Analytic Generator",
        # terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="matakov@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns += [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]

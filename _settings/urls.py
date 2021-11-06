import debug_toolbar
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("wb.urls")),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
]
urlpatterns += [
    path("__debug__/", include(debug_toolbar.urls)),
]

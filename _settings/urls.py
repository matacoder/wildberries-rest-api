import debug_toolbar
from django.conf import settings
from django.contrib import admin
from django.urls import include, path


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path("", include("wb.urls")),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("sentry-debug/", trigger_error),
]
urlpatterns += [
    path("__debug__/", include(debug_toolbar.urls)),
]

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include([
        path("auth/", include("users.urls.auth")),
        path("users/", include("users.urls.users")),
        path("academic/", include("academic.urls")),
        path("community/", include("community.urls")),
    ])),
]

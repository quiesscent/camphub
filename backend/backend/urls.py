from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include([
        path("auth/", include("users.urls.auth")),
        path("users/", include("users.urls.users")),
        path("academic/", include("academic.urls")),
        path("community/", include("community.urls")),
        path("messaging/", include("messaging.urls")),
        path("content/", include("content.urls.posts")),
    ])),
    # Swagger/OpenAPI documentation URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

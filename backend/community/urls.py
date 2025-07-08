from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, ClubViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'clubs', ClubViewSet, basename='club')

app_name = 'community'

urlpatterns = [
    path('', include(router.urls)),
]
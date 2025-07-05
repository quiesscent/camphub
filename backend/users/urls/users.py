from django.urls import path
from users.views import ProfileView, PublicProfileView, ChangePasswordView, InstitutionListView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("<int:user_id>/", PublicProfileView.as_view(), name="public_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("institutions/", InstitutionListView.as_view(), name="institutions"),
]

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .serializers import (
    RegisterSerializer, LoginSerializer, ChangePasswordSerializer, InstitutionSerializer
)
from .models import Institution

User = get_user_model()

API_VERSION = "1.0"

def api_response(success, data=None, message="", errors=None, status_code=200):
    return Response({
        "success": success,
        "data": data,
        "message": message,
        "errors": errors,
        "meta": {
            "timestamp": timezone.now().isoformat(),
            "version": API_VERSION,
        }
    }, status=status_code)

def send_verification_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
    
    subject = 'Verify your CampusConnect account'
    html_message = f"""
    <html>
    <body>
        <h2>Welcome to CampusConnect!</h2>
        <p>Hello {user.first_name},</p>
        <p>Thank you for registering with CampusConnect. Please click the link below to verify your email address:</p>
        <p><a href="{verification_url}">Verify Email Address</a></p>
        <p>If you didn't create this account, please ignore this email.</p>
        <p>Best regards,<br>The CampusConnect Team</p>
    </body>
    </html>
    """
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception:
        return False

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            email_sent = send_verification_email(user)
            
            resp_data = {
                "user_id": user.id,
                "email": user.email,
                "verification_required": True,
                "message": f"Verification email sent to {user.email}" if email_sent else "Registration successful. Email verification pending."
            }
            
            return api_response(
                True, 
                resp_data,
                "Registration successful. Please verify your email.",
                status_code=status.HTTP_201_CREATED
            )
        
        return api_response(
            False, 
            None, 
            "Registration failed", 
            serializer.errors, 
            status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    uid = request.data.get('uid')
    token = request.data.get('token')
    
    if not uid or not token:
        return api_response(
            False, 
            None, 
            "Missing verification parameters", 
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            
            return api_response(
                True, 
                {"user_id": user.id}, 
                "Email verified successfully"
            )
        else:
            return api_response(
                False, 
                None, 
                "Invalid verification token", 
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return api_response(
            False, 
            None, 
            "Invalid verification link", 
            status_code=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        profile = getattr(user, "profile", None)
        institution = profile.institution if profile else None
        
        data = {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_picture": user.profile_picture.url if user.profile_picture else None,
                "institution": {
                    "id": institution.id,
                    "name": institution.name,
                    "domain": institution.domain
                } if institution else None,
                "role": profile.role if profile else None,
                "is_verified": user.is_verified,
            }
        }
        return api_response(True, data, "Login successful")
    
    return api_response(
        False, 
        None, 
        "Login failed", 
        serializer.errors, 
        status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        outstanding_tokens = OutstandingToken.objects.filter(user=request.user)
        for token in outstanding_tokens:
            BlacklistedToken.objects.get_or_create(token=token)
        
        return api_response(True, None, "Successfully logged out")
    
    except Exception:
        return api_response(
            False, 
            None, 
            "Logout failed", 
            status_code=status.HTTP_400_BAD_REQUEST
        )

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return api_response(
                False, 
                None, 
                "refresh_token is required", 
                status_code=400
            )
        
        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            data = {
                "access_token": response.data.get("access"),
                "expires_in": 1800
            }
            return api_response(True, data, "Token refreshed successfully")
        
        return api_response(
            False, 
            None, 
            "Token refresh failed", 
            response.data, 
            response.status_code
        )

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, "profile", None)
        institution = profile.institution if profile else None
        campus = profile.campus if profile else None
        
        data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_picture": user.profile_picture.url if user.profile_picture else None,
            "bio": user.bio,
            "major": user.major,
            "graduation_year": user.graduation_year,
            "student_id": profile.student_id if profile else None,
            "dorm_building": profile.dorm_building if profile else None,
            "room_number": profile.room_number if profile else None,
            "institution": {
                "id": institution.id,
                "name": institution.name,
                "domain": institution.domain
            } if institution else None,
            "campus": {
                "id": campus.id,
                "name": campus.name,
                "address": campus.address
            } if campus else None,
            "privacy_settings": user.privacy_settings,
            "stats": {
                "posts_count": 0,
                "friends_count": 0,
                "study_groups_count": 0,
                "events_attending": 0
            },
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
        return api_response(True, data)

    def put(self, request):
        user = request.user
        profile = getattr(user, "profile", None)
        
        user_fields = ["first_name", "last_name", "bio", "major", "graduation_year", "privacy_settings"]
        profile_fields = ["dorm_building", "room_number"]
        
        for field in user_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        
        if profile:
            for field in profile_fields:
                if field in request.data:
                    setattr(profile, field, request.data[field])
            profile.save()
        
        return api_response(
            True, 
            {"id": user.id, "message": "Profile updated successfully"}
        )

class PublicProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        profile = getattr(user, "profile", None)
        institution = profile.institution if profile else None
        campus = profile.campus if profile else None
        
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_picture": user.profile_picture.url if user.profile_picture else None,
            "bio": user.bio,
            "major": user.major,
            "graduation_year": user.graduation_year,
            "institution": {
                "id": institution.id,
                "name": institution.name
            } if institution else None,
            "campus": {
                "id": campus.id,
                "name": campus.name
            } if campus else None,
            "is_friend": False,
            "mutual_friends_count": 0,
            "common_courses": [],
            "stats": {
                "posts_count": 0,
                "friends_count": 0
            }
        }
        return api_response(True, data)

class InstitutionListView(generics.ListAPIView):
    queryset = Institution.objects.filter(is_active=True)
    serializer_class = InstitutionSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, serializer.data, "Institutions retrieved successfully")

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = self.get_object()
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return api_response(
                True, 
                None, 
                "Password changed successfully"
            )
        
        return api_response(
            False, 
            None, 
            "Password change failed", 
            serializer.errors, 
            status.HTTP_400_BAD_REQUEST
        )

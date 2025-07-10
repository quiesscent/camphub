from rest_framework import permissions


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow organizers to edit events.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the organizer
        return obj.organizer == request.user


class IsClubOfficerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow club officers/presidents to edit clubs.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to club officers and presidents
        membership = obj.members.filter(
            user=request.user,
            is_active=True,
            role__in=['officer', 'president']
        ).first()
        
        return membership is not None


class CanManageClubMembers(permissions.BasePermission):
    """
    Custom permission for managing club memberships.
    """
    
    def has_permission(self, request, view):
        # Only authenticated users can manage memberships
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Club object - check if user can manage club
        if hasattr(obj, 'members'):
            membership = obj.members.filter(
                user=request.user,
                is_active=True,
                role__in=['officer', 'president']
            ).first()
            return membership is not None
        
        # ClubMember object - check if user can manage the club
        if hasattr(obj, 'club'):
            membership = obj.club.members.filter(
                user=request.user,
                is_active=True,
                role__in=['officer', 'president']
            ).first()
            return membership is not None
        
        return False
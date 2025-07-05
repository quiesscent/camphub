from django.urls import path, include
from .views import (
    CourseListView, CourseDetailView, CourseCreateView,
    CourseEnrollmentsView, CourseStudyGroupsView,
    StudyGroupListView, StudyGroupDetailView, StudyGroupCreateView,
    StudyGroupMembersView, AcademicDashboardView,
    enroll_in_course, unenroll_from_course,
    join_study_group, leave_study_group
)

app_name = 'academic'

urlpatterns = [
    # Course URLs
    path('courses/', CourseListView.as_view(), name='course_list'),
    path('courses/create/', CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:course_id>/enroll/', enroll_in_course, name='enroll_course'),
    path('courses/<int:course_id>/unenroll/', unenroll_from_course, name='unenroll_course'),
    path('courses/<int:course_id>/enrollments/', CourseEnrollmentsView.as_view(), name='course_enrollments'),
    path('courses/<int:course_id>/study-groups/', CourseStudyGroupsView.as_view(), name='course_study_groups'),
    
    # Study Group URLs
    path('study-groups/', StudyGroupListView.as_view(), name='study_group_list'),
    path('study-groups/create/', StudyGroupCreateView.as_view(), name='study_group_create'),
    path('study-groups/<int:pk>/', StudyGroupDetailView.as_view(), name='study_group_detail'),
    path('study-groups/<int:group_id>/join/', join_study_group, name='join_study_group'),
    path('study-groups/<int:group_id>/leave/', leave_study_group, name='leave_study_group'),
    path('study-groups/<int:group_id>/members/', StudyGroupMembersView.as_view(), name='study_group_members'),
    
    # Dashboard
    path('dashboard/', AcademicDashboardView.as_view(), name='academic_dashboard'),
]
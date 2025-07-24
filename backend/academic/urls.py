from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    # Course endpoints
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course-create'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_in_course, name='course-enroll'),
    path('courses/<int:course_id>/unenroll/', views.unenroll_from_course, name='course-unenroll'),
    path('courses/<int:course_id>/enrollments/', views.CourseEnrollmentsView.as_view(), name='course-enrollments'),
    path('courses/<int:course_id>/study-groups/', views.CourseStudyGroupsView.as_view(), name='course-study-groups'),
    
    # Study group endpoints
    path('study-groups/', views.StudyGroupListView.as_view(), name='study-group-list'),
    path('study-groups/create/', views.StudyGroupCreateView.as_view(), name='study-group-create'),
    path('study-groups/<int:pk>/', views.StudyGroupDetailView.as_view(), name='study-group-detail'),
    path('study-groups/<int:group_id>/join/', views.join_study_group, name='study-group-join'),
    path('study-groups/<int:group_id>/leave/', views.leave_study_group, name='study-group-leave'),
    path('study-groups/<int:group_id>/members/', views.StudyGroupMembersView.as_view(), name='study-group-members'),
    
    # Dashboard endpoint
    path('dashboard/', views.AcademicDashboardView.as_view(), name='academic-dashboard'),
]
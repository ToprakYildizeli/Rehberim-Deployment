from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import api_views

urlpatterns = [
    # Auth
    path("auth/login/", api_views.LoginView.as_view(), name="api-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api-refresh"),
    path("auth/logout/", api_views.LogoutView.as_view(), name="api-logout"),
    path("auth/me/", api_views.MeView.as_view(), name="api-me"),

    # Kayıt (rol başına)
    path("auth/register/counselor/", api_views.CounselorRegisterView.as_view(), name="api-register-counselor"),
    path("auth/register/student/", api_views.StudentRegisterView.as_view(), name="api-register-student"),
    path("auth/register/parent/", api_views.ParentRegisterView.as_view(), name="api-register-parent"),

    # Rehberin öğrenci listesi
    path("students/", api_views.CounselorStudentsView.as_view(), name="api-students"),

    # Bağlanma
    path("students/connect-counselor/", api_views.ConnectCounselorView.as_view(), name="api-connect-counselor"),
    path("parents/connect-student/", api_views.ConnectStudentView.as_view(), name="api-connect-student"),
]

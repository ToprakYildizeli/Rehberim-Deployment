from django.urls import path
from . import views

#URLconf
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard-alt'),
    path('students/', views.students, name='students'),
    path("students/<int:id>", views.studentID, name='student-detail'),
    path("settings/", views.settings, name='settings'),
]
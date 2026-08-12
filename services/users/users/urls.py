from django.urls import path
from .views import (
    RegisterView, LoginView, TokenRefreshView, LogoutView, CurrentUserView,
    ProfileView, ProfileDetailView, ChangePasswordView
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('refresh', TokenRefreshView.as_view(), name='refresh'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('me', CurrentUserView.as_view(), name='me'),
    path('change-password', ChangePasswordView.as_view(), name='change_password'),
    path('profile', ProfileView.as_view(), name='profile'),
    path('profile/detail', ProfileDetailView.as_view(), name='profile_detail'),
]

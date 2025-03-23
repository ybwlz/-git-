from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # 用户认证
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # 用户个人资料
    path('profile/', views.UserProfileView.profile_view, name='profile'),
    path('change-password/', views.UserProfileView.change_password, name='change_password'),
    
    # 密码重置
    path('password-reset/', views.PasswordResetView.password_reset_request, name='password_reset_request'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

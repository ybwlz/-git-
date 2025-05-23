from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # 用户相关路由
    path('login/', views.login_view, name='user_login'),
    path('logout/', views.logout_view, name='user_logout'),
    path('register/', views.register_view, name='register'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/verify/', views.password_reset_verify_view, name='password_reset_verify'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
]

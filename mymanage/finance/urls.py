from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # 示例URL模式，后续根据实际需要添加
    path('payments/', views.payment_list, name='payments'),
    path('payment/create/', views.create_payment, name='create_payment'),
]

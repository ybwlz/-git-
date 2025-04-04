from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # 付款记录
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_add, name='payment_add'),
    path('payments/<int:payment_id>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:payment_id>/delete/', views.payment_delete, name='payment_delete'),
    path('payments/<int:payment_id>/mark-as-paid/', views.mark_as_paid, name='mark_as_paid'),
    # 导出功能
    path('payments/export/', views.payment_export, name='payment_export'),
]

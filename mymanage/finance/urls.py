from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # 支付记录相关URL
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    
    # 支付类别相关URL
    path('categories/', views.payment_category_list, name='payment_category_list'),
    path('categories/create/', views.payment_category_create, name='payment_category_create'),
    path('categories/<int:pk>/edit/', views.payment_category_edit, name='payment_category_edit'),
    
    # 学费相关URL
    path('tuition/', views.tuition_list, name='tuition_list'),
    path('tuition/create/', views.tuition_create, name='tuition_create'),
    path('tuition/<int:pk>/', views.tuition_detail, name='tuition_detail'),
    path('tuition/<int:tuition_id>/payment/', views.tuition_payment_create, name='tuition_payment_create'),
    path('tuition/<int:tuition_id>/invoice/', views.invoice_generate, name='invoice_generate'),
    
    # 支出相关URL
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    
    # 报表相关URL
    path('reports/', views.financial_report, name='financial_report'),
    
    # AJAX请求URL
    path('api/get-course-tuition/', views.get_course_tuition, name='get_course_tuition'),
]

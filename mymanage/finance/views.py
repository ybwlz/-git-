from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator

from mymanage.users.models import User
from mymanage.students.models import Student
from mymanage.courses.models import Course, Enrollment
from .models import Payment, PaymentCategory, Tuition, TuitionPayment, Expense
from .forms import (
    PaymentForm, PaymentCategoryForm, TuitionForm, 
    TuitionPaymentForm, ExpenseForm, FinancialReportForm
)


@login_required
def payment_list(request):
    """
    显示所有支付记录列表
    """
    # 根据用户角色过滤不同的支付记录
    if request.user.user_type == 'admin':
        payments = Payment.objects.all().order_by('-payment_date')
    elif request.user.user_type == 'teacher':
        payments = Payment.objects.filter(teacher=request.user.teacher).order_by('-payment_date')
    else:
        # 学生只能看自己的支付记录
        try:
            student = Student.objects.get(user=request.user)
            payments = Payment.objects.filter(student=student).order_by('-payment_date')
        except Student.DoesNotExist:
            payments = Payment.objects.none()
    
    # 分页处理
    paginator = Paginator(payments, 20)  # 每页显示20条记录
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_amount': payments.aggregate(total=Sum('amount'))['total'] or 0
    }
    return render(request, 'finance/payment_list.html', context)


@login_required
def payment_create(request):
    """
    创建新的支付记录
    """
    # 检查权限，只有管理员和教师可以创建支付记录
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, '您没有权限创建支付记录')
        return redirect('finance:payment_list')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.recorded_by = request.user
            payment.save()
            messages.success(request, '支付记录创建成功')
            return redirect('finance:payment_list')
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'title': '创建新支付记录'
    }
    return render(request, 'finance/payment_form.html', context)


@login_required
def payment_detail(request, pk):
    """
    显示支付记录详情
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    # 检查用户权限
    if request.user.user_type == 'student':
        try:
            student = Student.objects.get(user=request.user)
            if payment.student != student:
                messages.error(request, '您没有权限查看此支付记录')
                return redirect('finance:payment_list')
        except Student.DoesNotExist:
            messages.error(request, '您没有权限查看此支付记录')
            return redirect('finance:payment_list')
    
    context = {
        'payment': payment
    }
    return render(request, 'finance/payment_detail.html', context)


@login_required
def payment_category_list(request):
    """
    显示所有支付类别列表
    """
    # 只有管理员可以查看支付类别
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限查看支付类别')
        return redirect('finance:payment_list')
    
    categories = PaymentCategory.objects.all().order_by('category_type', 'name')
    
    context = {
        'categories': categories
    }
    return render(request, 'finance/payment_category_list.html', context)


@login_required
def payment_category_create(request):
    """
    创建新的支付类别
    """
    # 只有管理员可以创建支付类别
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限创建支付类别')
        return redirect('finance:payment_list')
    
    if request.method == 'POST':
        form = PaymentCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '支付类别创建成功')
            return redirect('finance:payment_category_list')
    else:
        form = PaymentCategoryForm()
    
    context = {
        'form': form,
        'title': '创建新支付类别'
    }
    return render(request, 'finance/payment_category_form.html', context)


@login_required
def payment_category_edit(request, pk):
    """
    编辑支付类别
    """
    # 只有管理员可以编辑支付类别
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限编辑支付类别')
        return redirect('finance:payment_list')
    
    category = get_object_or_404(PaymentCategory, pk=pk)
    
    if request.method == 'POST':
        form = PaymentCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '支付类别更新成功')
            return redirect('finance:payment_category_list')
    else:
        form = PaymentCategoryForm(instance=category)
    
    context = {
        'form': form,
        'title': '编辑支付类别'
    }
    return render(request, 'finance/payment_category_form.html', context)


@login_required
def tuition_list(request):
    """
    显示学费记录列表
    """
    # 根据用户角色过滤不同的学费记录
    if request.user.user_type == 'admin':
        tuitions = Tuition.objects.all().order_by('-created_at')
    elif request.user.user_type == 'teacher':
        # 教师只能看到其教授课程的学费记录
        teacher_courses = Course.objects.filter(teacher=request.user.teacher)
        tuitions = Tuition.objects.filter(course__in=teacher_courses).order_by('-created_at')
    else:
        # 学生只能看自己的学费记录
        try:
            student = Student.objects.get(user=request.user)
            tuitions = Tuition.objects.filter(student=student).order_by('-created_at')
        except Student.DoesNotExist:
            tuitions = Tuition.objects.none()
    
    # 分页处理
    paginator = Paginator(tuitions, 20)  # 每页显示20条记录
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_amount': tuitions.aggregate(total=Sum('amount'))['total'] or 0,
        'total_paid': tuitions.aggregate(total=Sum('paid_amount'))['total'] or 0,
        'total_remaining': tuitions.aggregate(
            total=Sum(F('amount') - F('paid_amount'))
        )['total'] or 0
    }
    return render(request, 'finance/tuition_list.html', context)


@login_required
def tuition_create(request):
    """
    创建新的学费记录
    """
    # 检查权限，只有管理员可以创建学费记录
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限创建学费记录')
        return redirect('finance:tuition_list')
    
    if request.method == 'POST':
        form = TuitionForm(request.POST)
        if form.is_valid():
            tuition = form.save(commit=False)
            tuition.enrollment = form.cleaned_data['enrollment']
            tuition.recorded_by = request.user
            tuition.save()
            messages.success(request, '学费记录创建成功')
            return redirect('finance:tuition_list')
    else:
        form = TuitionForm()
    
    context = {
        'form': form,
        'title': '创建新学费记录'
    }
    return render(request, 'finance/tuition_form.html', context)


@login_required
def tuition_detail(request, pk):
    """
    显示学费记录详情
    """
    tuition = get_object_or_404(Tuition, pk=pk)
    
    # 检查用户权限
    if request.user.user_type == 'student':
        try:
            student = Student.objects.get(user=request.user)
            if tuition.student != student:
                messages.error(request, '您没有权限查看此学费记录')
                return redirect('finance:tuition_list')
        except Student.DoesNotExist:
            messages.error(request, '您没有权限查看此学费记录')
            return redirect('finance:tuition_list')
    elif request.user.user_type == 'teacher':
        if tuition.course.teacher != request.user.teacher:
            messages.error(request, '您没有权限查看此学费记录')
            return redirect('finance:tuition_list')
    
    # 获取此学费记录的所有支付记录
    payments = tuition.tuition_payments.all().order_by('-payment_date')
    
    # 如果是管理员，显示缴费表单
    payment_form = None
    if request.user.user_type == 'admin':
        payment_form = TuitionPaymentForm(user=request.user, tuition_id=tuition.id)
    
    context = {
        'tuition': tuition,
        'payments': payments,
        'payment_form': payment_form
    }
    return render(request, 'finance/tuition_detail.html', context)


@login_required
def tuition_payment_create(request, tuition_id):
    """
    为学费记录创建新的支付记录
    """
    # 检查权限，只有管理员可以创建学费支付记录
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限创建学费支付记录')
        return redirect('finance:tuition_list')
    
    tuition = get_object_or_404(Tuition, pk=tuition_id)
    
    if request.method == 'POST':
        form = TuitionPaymentForm(request.POST, user=request.user, tuition_id=tuition_id)
        if form.is_valid():
            payment = form.save()
            
            # 更新学费记录状态
            tuition.update_status()
            
            messages.success(request, '学费支付记录创建成功')
            return redirect('finance:tuition_detail', pk=tuition_id)
    else:
        form = TuitionPaymentForm(user=request.user, tuition_id=tuition_id)
    
    context = {
        'form': form,
        'tuition': tuition,
        'title': '创建新学费支付记录'
    }
    return render(request, 'finance/tuition_payment_form.html', context)


@login_required
def expense_list(request):
    """
    显示支出记录列表
    """
    # 检查权限，只有管理员可以查看所有支出记录
    if request.user.user_type == 'admin':
        expenses = Expense.objects.all().order_by('-expense_date')
    elif request.user.user_type == 'teacher':
        # 教师只能看到与自己相关的支出记录
        expenses = Expense.objects.filter(teacher=request.user.teacher).order_by('-expense_date')
    else:
        messages.error(request, '您没有权限查看支出记录')
        return redirect('home')
    
    # 分页处理
    paginator = Paginator(expenses, 20)  # 每页显示20条记录
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_amount': expenses.aggregate(total=Sum('amount'))['total'] or 0
    }
    return render(request, 'finance/expense_list.html', context)


@login_required
def expense_create(request):
    """
    创建新的支出记录
    """
    # 检查权限，只有管理员可以创建支出记录
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限创建支出记录')
        return redirect('finance:expense_list')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save()
            messages.success(request, '支出记录创建成功')
            return redirect('finance:expense_list')
    else:
        form = ExpenseForm(user=request.user)
    
    context = {
        'form': form,
        'title': '创建新支出记录'
    }
    return render(request, 'finance/expense_form.html', context)


@login_required
def expense_detail(request, pk):
    """
    显示支出记录详情
    """
    expense = get_object_or_404(Expense, pk=pk)
    
    # 检查用户权限
    if request.user.user_type == 'teacher':
        if expense.teacher != request.user.teacher:
            messages.error(request, '您没有权限查看此支出记录')
            return redirect('finance:expense_list')
    elif request.user.user_type != 'admin':
        messages.error(request, '您没有权限查看支出记录')
        return redirect('home')
    
    context = {
        'expense': expense
    }
    return render(request, 'finance/expense_detail.html', context)


@login_required
def financial_report(request):
    """
    生成财务报表
    """
    # 检查权限，只有管理员可以查看财务报表
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限查看财务报表')
        return redirect('home')
    
    # 处理表单提交
    if request.method == 'POST':
        form = FinancialReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # 根据报表类型生成不同的报表数据
            report_data = generate_report_data(report_type, start_date, end_date)
            
            context = {
                'form': form,
                'report_type': report_type,
                'start_date': start_date,
                'end_date': end_date,
                'report_data': report_data
            }
            return render(request, 'finance/financial_report.html', context)
    else:
        form = FinancialReportForm()
    
    context = {
        'form': form
    }
    return render(request, 'finance/financial_report.html', context)


def generate_report_data(report_type, start_date, end_date):
    """
    根据报表类型和日期范围生成报表数据
    """
    report_data = {
        'summary': {},
        'details': [],
        'chart_data': {}
    }
    
    if report_type == 'income':
        # 收入报表
        income_payments = Payment.objects.filter(
            category__category_type='income',
            payment_date__range=[start_date, end_date]
        )
        
        # 汇总数据
        total_income = income_payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # 按类别分类的收入
        income_by_category = income_payments.values(
            'category__name'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # 按月份分类的收入
        income_by_month = income_payments.annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # 每日收入明细
        daily_income = income_payments.values(
            'payment_date'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-payment_date')
        
        report_data['summary'] = {
            'total_income': total_income,
            'total_transactions': income_payments.count(),
            'avg_income': total_income / income_payments.count() if income_payments.count() > 0 else 0
        }
        
        report_data['details'] = {
            'income_by_category': income_by_category,
            'daily_income': daily_income
        }
        
        # 准备图表数据
        report_data['chart_data'] = {
            'categories': [item['category__name'] for item in income_by_category],
            'amounts': [float(item['total']) for item in income_by_category],
            'months': [item['month'].strftime('%Y-%m') for item in income_by_month],
            'monthly_amounts': [float(item['total']) for item in income_by_month]
        }
        
    elif report_type == 'expense':
        # 支出报表
        expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date]
        )
        
        # 汇总数据
        total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0
        
        # 按类型分类的支出
        expense_by_type = expenses.values(
            'expense_type'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # 按月份分类的支出
        expense_by_month = expenses.annotate(
            month=TruncMonth('expense_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # 每日支出明细
        daily_expense = expenses.values(
            'expense_date'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-expense_date')
        
        report_data['summary'] = {
            'total_expense': total_expense,
            'total_transactions': expenses.count(),
            'avg_expense': total_expense / expenses.count() if expenses.count() > 0 else 0
        }
        
        report_data['details'] = {
            'expense_by_type': expense_by_type,
            'daily_expense': daily_expense
        }
        
        # 准备图表数据
        report_data['chart_data'] = {
            'categories': [item['expense_type'] for item in expense_by_type],
            'amounts': [float(item['total']) for item in expense_by_type],
            'months': [item['month'].strftime('%Y-%m') for item in expense_by_month],
            'monthly_amounts': [float(item['total']) for item in expense_by_month]
        }
        
    elif report_type == 'tuition':
        # 学费报表
        tuitions = Tuition.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        # 汇总数据
        total_tuition = tuitions.aggregate(total=Sum('amount'))['total'] or 0
        total_paid = tuitions.aggregate(total=Sum('paid_amount'))['total'] or 0
        total_remaining = total_tuition - total_paid
        
        # 按状态分类的学费记录
        tuition_by_status = tuitions.values(
            'status'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('status')
        
        # 按课程分类的学费记录
        tuition_by_course = tuitions.values(
            'course__name'
        ).annotate(
            total=Sum('amount'),
            paid=Sum('paid_amount'),
            count=Count('id')
        ).order_by('-total')
        
        report_data['summary'] = {
            'total_tuition': total_tuition,
            'total_paid': total_paid,
            'total_remaining': total_remaining,
            'payment_rate': (total_paid / total_tuition * 100) if total_tuition > 0 else 0,
            'total_students': tuitions.values('student').distinct().count()
        }
        
        report_data['details'] = {
            'tuition_by_status': tuition_by_status,
            'tuition_by_course': tuition_by_course
        }
        
        # 准备图表数据
        report_data['chart_data'] = {
            'status_labels': [item['status'] for item in tuition_by_status],
            'status_counts': [item['count'] for item in tuition_by_status],
            'status_amounts': [float(item['total']) for item in tuition_by_status],
            'course_names': [item['course__name'] for item in tuition_by_course],
            'course_amounts': [float(item['total']) for item in tuition_by_course],
            'course_paid': [float(item['paid']) for item in tuition_by_course]
        }
        
    elif report_type == 'profit':
        # 收支利润报表
        # 计算收入
        income_payments = Payment.objects.filter(
            category__category_type='income',
            payment_date__range=[start_date, end_date]
        )
        total_income = income_payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # 计算支出
        expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date]
        )
        total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0
        
        # 按月统计收入和支出
        income_by_month = income_payments.annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        expense_by_month = expenses.annotate(
            month=TruncMonth('expense_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # 合并月度数据
        monthly_data = {}
        for item in income_by_month:
            month_str = item['month'].strftime('%Y-%m')
            if month_str not in monthly_data:
                monthly_data[month_str] = {'income': 0, 'expense': 0, 'profit': 0}
            monthly_data[month_str]['income'] = float(item['total'])
        
        for item in expense_by_month:
            month_str = item['month'].strftime('%Y-%m')
            if month_str not in monthly_data:
                monthly_data[month_str] = {'income': 0, 'expense': 0, 'profit': 0}
            monthly_data[month_str]['expense'] = float(item['total'])
        
        # 计算每月利润
        for month, data in monthly_data.items():
            data['profit'] = data['income'] - data['expense']
        
        # 获取排序后的月份列表
        sorted_months = sorted(monthly_data.keys())
        
        report_data['summary'] = {
            'total_income': total_income,
            'total_expense': total_expense,
            'total_profit': total_income - total_expense,
            'profit_margin': ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
        }
        
        report_data['details'] = {
            'monthly_data': [{'month': month, **monthly_data[month]} for month in sorted_months]
        }
        
        # 准备图表数据
        report_data['chart_data'] = {
            'months': sorted_months,
            'income_data': [monthly_data[month]['income'] for month in sorted_months],
            'expense_data': [monthly_data[month]['expense'] for month in sorted_months],
            'profit_data': [monthly_data[month]['profit'] for month in sorted_months]
        }
    
    return report_data


@login_required
def invoice_generate(request, tuition_id):
    """
    为学费记录生成发票/收据
    """
    # 检查权限，只有管理员可以生成发票
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限生成发票')
        return redirect('finance:tuition_list')
    
    tuition = get_object_or_404(Tuition, pk=tuition_id)
    
    # 这里可以使用第三方库如reportlab生成PDF发票
    # 简化版，先生成一个HTML版本
    context = {
        'tuition': tuition,
        'payments': tuition.tuition_payments.all().order_by('-payment_date'),
        'generated_time': timezone.now(),
        'invoice_number': f"INV-{tuition.id}-{timezone.now().strftime('%Y%m%d%H%M')}"
    }
    
    return render(request, 'finance/invoice_template.html', context)


@login_required
def get_course_tuition(request):
    """
    AJAX请求：获取课程的学费金额
    """
    course_id = request.GET.get('course_id')
    if not course_id:
        return JsonResponse({'error': '未提供课程ID'}, status=400)
    
    try:
        course = Course.objects.get(pk=course_id)
        # 假设课程模型有一个tuition_fee字段或者其他费用计算逻辑
        tuition_fee = getattr(course, 'tuition_fee', 0)
        return JsonResponse({'amount': tuition_fee})
    except Course.DoesNotExist:
        return JsonResponse({'error': '课程不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
from django.urls import reverse
from django.db import connection
from django.core.exceptions import ValidationError
import logging
import uuid as uuid_lib
from django.views.decorators.csrf import csrf_exempt

from mymanage.users.decorators import teacher_required
from .models import TeacherProfile, TeacherCertificate, PrivacySetting
from .forms import TeacherProfileForm, TeacherCertificateForm, TeacherRegistrationForm, PrivacySettingForm, PasswordChangeForm
from mymanage.students.models import Student, PracticeRecord
from mymanage.courses.models import Course, CourseSchedule, SheetMusic, PianoLevel, Piano
from mymanage.attendance.models import AttendanceRecord, AttendanceSession, QRCode, WaitingQueue
from mymanage.finance.models import Payment, PaymentCategory, Fee

# 设置日志记录器
logger = logging.getLogger(__name__)

@login_required
@teacher_required
def teacher_dashboard(request):
    """教师仪表板"""
    teacher = request.user.teacher_profile
    
    # 自动关闭过期的考勤会话
    from mymanage.attendance.models import AttendanceSession
    current_time = timezone.now()
    
    # 1. 关闭所有已过期但仍标记为活跃的会话
    expired_sessions = AttendanceSession.objects.filter(
        status='active',
        end_time__lt=current_time
    )
    for session in expired_sessions:
        session.status = 'closed'
        session.is_active = False
        session.save()
    
    # 2. 确保每个老师只有一个活跃会话
    active_sessions = AttendanceSession.objects.filter(
        created_by=request.user,
        status='active'
    ).order_by('-start_time')
    
    # 如果有多个活跃会话，保留最新的一个，关闭其他的
    if active_sessions.count() > 1:
        keep_session = active_sessions.first()
        for session in active_sessions[1:]:
            session.status = 'closed'
            session.is_active = False
            session.end_time = current_time
            session.save()
    
    # 查询最近活跃的考勤会话
    active_sessions = AttendanceSession.objects.filter(
        created_by=request.user,
        status='active'
    ).order_by('-start_time')[:5]
    
    # 获取所有学生数量（修改为获取所有学生）
    students_count = Student.objects.count()
    
    # 获取课程数量
    courses_count = Course.objects.filter(teacher=teacher).count()
    
    # 获取今日考勤记录数
    today = timezone.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    # 使用原始SQL查询确保准确匹配日期字符串
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT ar.student_id) 
            FROM attendance_attendancerecord ar
            JOIN attendance_attendancesession ats ON ar.session_id = ats.id
            JOIN courses_course cc ON ats.course_id = cc.id
            WHERE DATE(ar.check_in_time) = %s
        """, [today_str])
        attendance_today = cursor.fetchone()[0]
    
    # 使用ORM查询
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    attendance_today_orm = AttendanceRecord.objects.filter(
        check_in_time__gte=today_start,
        check_in_time__lte=today_end
    ).values('student').distinct().count()
    
    print(f"DEBUG - 今日日期: {today}")
    print(f"DEBUG - 实际签到学生数: {attendance_today}")
    
    
    # 获取本月收入
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    payments_this_month = Payment.objects.filter(
        status='paid',
        payment_date__gte=start_of_month,
        payment_date__lte=today
    ).aggregate(total=Sum('amount'))
    
    # 获取年度收入
    year_start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    yearly_income = Payment.objects.filter(
        status='paid',
        payment_date__gte=year_start,
        payment_date__lte=today
    ).aggregate(total=Sum('amount'))
    
    # 获取待缴学费
    pending_payments = Payment.objects.filter(
        status='pending'
    ).aggregate(total=Sum('amount'))
    
    # 最近的考勤会话 - 确保不包含重复或异常会话
    # 先关闭任何异常的会话（开始时间相同的会话）
    duplicate_sessions = AttendanceSession.objects.values('start_time').filter(
        course__teacher=teacher
    ).annotate(count=Count('id')).filter(count__gt=1)
    
    for dup in duplicate_sessions:
        dup_time = dup['start_time']
        dup_sessions = AttendanceSession.objects.filter(
            course__teacher=teacher,
            start_time=dup_time
        ).order_by('-id')
        
        # 保留最新的一个，关闭其他的
        if dup_sessions.count() > 1:
            keep_session = dup_sessions.first()
            for session in dup_sessions[1:]:  # 跳过第一个
                session.status = 'closed'
                session.is_active = False
                session.save()
                print(f"DEBUG - 关闭重复会话: ID={session.id}, 课程={session.course.name}")
    
    # 获取最近的考勤会话（确保获取的都是有效的）
    recent_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher
    ).order_by('-start_time')[:5]
    
    # 获取学生等级分布数据
    student_levels = []
    for i in range(1, 11):
        level_name = f"{i}级"
        # 修改为获取所有学生的等级分布
        count = Student.objects.filter(
            level=i
        ).count()
        student_levels.append({
            'name': level_name,
            'count': count
        })
    
    # 重新获取活跃的考勤会话及二维码（在关闭过期会话后）
    active_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        status='active'
    ).order_by('-start_time')
    
    current_qrcode = None
    qrcode_expiry_time = None
    
    # 如果有活跃的考勤会话，尝试获取其二维码
    if active_sessions.exists():
        active_session = active_sessions.first()
        if hasattr(active_session, 'qrcode') and active_session.qrcode:
            qrcode = active_session.qrcode
            if qrcode.is_valid():
                # 获取二维码图片URL
                current_qrcode = qrcode.qr_code_image.url if qrcode.qr_code_image else None
                qrcode_expiry_time = qrcode.expires_at
    
    context = {
        'teacher': teacher,  # 添加教师对象到上下文
        'students_count': students_count,
        'courses_count': courses_count,
        'attendance_today': attendance_today,
        'payments_this_month': payments_this_month.get('total', 0),
        'recent_sessions': recent_sessions,
        'student_levels': student_levels,
        'yearly_income': yearly_income.get('total', 0),
        'pending_payments': pending_payments.get('total', 0),
        'current_time': current_time,  # 添加当前时间到上下文
        'unread_notifications_count': 0,  # 为模板提供默认值
        'current_qrcode': current_qrcode,  # 添加当前二维码到上下文
        'qrcode_expiry_time': qrcode_expiry_time,  # 添加二维码过期时间到上下文
    }
    
    return render(request, 'teachers/teacher_dashboard.html', context)


@login_required
@teacher_required
def teacher_profile(request):
    """教师个人资料"""
    teacher = request.user.teacher_profile
    certificates = TeacherCertificate.objects.filter(teacher=teacher)
    
    # 获取或创建教师个人信息
    teacher_profile, created = TeacherProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.username,
            'specialties': ['钢琴基础课']
        }
    )
    
    # 获取或创建隐私设置
    privacy_settings, created = PrivacySetting.objects.get_or_create(
        teacher=teacher_profile
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 检查是否为Ajax请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if action == 'update_profile':
            # 手动处理表单字段
            teacher_profile.name = request.POST.get('name', teacher_profile.name)
            teacher_profile.gender = request.POST.get('gender', teacher_profile.gender)
            teacher_profile.phone = request.POST.get('phone', teacher_profile.phone)
            teacher_profile.bio = request.POST.get('bio', teacher_profile.bio)
            
            # 更新专长（多选字段）
            teacher_profile.specialties = request.POST.getlist('specialties')
            
            # 处理文件上传
            if 'avatar' in request.FILES:
                teacher_profile.avatar = request.FILES['avatar']
            
            # 保存教师个人资料
            teacher_profile.save()
            
            # 直接更新用户邮箱
            email = request.POST.get('email')
            if email and email != request.user.email:
                request.user.email = email
                request.user.save(update_fields=['email'])
            
            # 如果是Ajax请求，返回JSON响应
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': '个人信息已更新'
                })
            else:
                # 非Ajax请求，使用常规重定向
                return redirect(reverse('teachers:profile') + '?success_message=1')
        
        elif action == 'update_privacy':
            form = PrivacySettingForm(request.POST, instance=privacy_settings)
            if form.is_valid():
                form.save()
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': '隐私设置已更新'
                    })
                else:
                    messages.success(request, '隐私设置更新成功！')
                    return redirect('teachers:profile')
            elif is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '表单验证失败',
                    'errors': form.errors
                })
        
        elif action == 'change_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # 验证密码
            if not old_password or not new_password or not confirm_password:
                error_message = '所有密码字段都是必填的'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                else:
                    messages.error(request, error_message)
                    return redirect('teachers:profile')
            
            if new_password != confirm_password:
                error_message = '新密码和确认密码不匹配'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                else:
                    messages.error(request, error_message)
                    return redirect('teachers:profile')
            
            if not request.user.check_password(old_password):
                error_message = '当前密码不正确'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                else:
                    messages.error(request, error_message)
                    return redirect('teachers:profile')
            
            # 更新密码
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': '密码已成功修改'
                })
            else:
                messages.success(request, '密码修改成功！')
                return redirect('teachers:profile')
        
        elif action == 'update_avatar':
            # 处理头像上传
            if 'avatar' in request.FILES:
                avatar_file = request.FILES['avatar']
                teacher_profile.avatar = avatar_file
                teacher_profile.save(update_fields=['avatar'])
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': '头像已更新',
                        'avatar_url': teacher_profile.avatar.url
                    })
                else:
                    return redirect(reverse('teachers:profile') + '?success_message=1')
            else:
                error_message = '未提供头像文件'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                else:
                    return redirect('teachers:profile')
    
    context = {
        'teacher': teacher,
        'certificates': certificates,
        'teacher_profile': teacher_profile,
        'privacy_settings': privacy_settings,
        'profile_form': TeacherProfileForm(instance=teacher_profile),
        'privacy_form': PrivacySettingForm(instance=privacy_settings),
        'password_form': PasswordChangeForm(),
        'student_count': 0,  # 这里需要关联学生模型
        'total_lessons': 0,  # 这里需要关联课程模型
        'rating': 5.0,  # 这里需要关联评分模型
        'unread_notifications_count': 0,  # 为模板提供默认值
    }
    
    return render(request, 'teachers/teacher_profile.html', context)


@login_required
@teacher_required
def update_profile(request):
    """更新教师个人资料"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        # 处理表单提交
        teacher.name = request.POST.get('name')
        teacher.phone = request.POST.get('phone')
        teacher.gender = request.POST.get('gender')
        teacher.bio = request.POST.get('bio')
        
        if 'avatar' in request.FILES:
            teacher.avatar = request.FILES['avatar']
        
        teacher.save()
        messages.success(request, '个人资料更新成功')
        return redirect('teacher_profile')
    
    return render(request, 'teachers/teacher_profile_update.html', {'teacher': teacher})


@login_required
@teacher_required
def teacher_students(request):
    """教师的学生列表"""
    teacher = request.user.teacher_profile
    
    # 获取搜索参数
    search_query = request.GET.get('search', '')
    
    # 修改查询逻辑：获取所有学生，而不仅仅是与当前教师关联的学生
    students = Student.objects.all()
    
    # 应用搜索过滤
    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) | 
            Q(phone__icontains=search_query)
        )
    
    # 统计数据
    total_students = students.count()
    
    # 本月新增学生数
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_students_this_month = Student.objects.filter(
        created_at__gte=first_day_of_month
    ).distinct().count()
    
    # 等级分布
    level_distribution = {}
    for level in range(1, 11):
        level_distribution[level] = students.filter(level=level).count()
    
    # 最近加入的5名学生
    recent_students = students.order_by('-created_at')[:5]
    
    # 检查会话是否包含学生更新消息，如果有，将其转换为消息并清除会话变量
    student_updated = request.session.pop('student_updated', None)
    if student_updated:
        messages.success(request, f'学生"{student_updated["name"]}"信息已更新')
    
    # 获取今日开始时间
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 计算今日出勤率而不是平均出勤率
    # 获取今日应该出勤的学生总数（所有与教师相关的学生）
    today_enrolled_students = Student.objects.filter(courses__teacher=teacher).distinct().count()
    
    # 获取今日有出勤记录的学生数量
    today_attended_students = AttendanceRecord.objects.filter(
        check_in_time__gte=today_start,
        session__course__teacher=teacher
    ).values('student').distinct().count()
    
    # 计算今日出勤率，避免除以零错误
    today_attendance_rate = 0
    if today_enrolled_students > 0:
        today_attendance_rate = (today_attended_students / today_enrolled_students) * 100
    
    # 获取今日练琴人数
    today_attendance = AttendanceRecord.objects.filter(
        check_in_time__gte=today_start,
        session__course__teacher=teacher
    ).values('student').distinct().count()
    
    # 为每个学生添加练琴统计数据
    for student in students:
        # 计算总练琴时长（分钟）
        total_minutes = PracticeRecord.objects.filter(
            student=student
        ).aggregate(total=Sum('duration'))['total'] or 0
        
        # 将分钟转换为小时
        student.total_practice_time = round(total_minutes / 60, 1)
        
        # 获取最后练琴时间
        last_practice = PracticeRecord.objects.filter(
            student=student
        ).order_by('-date').first()
        
        student.last_practice = last_practice.date if last_practice else None
        
        # 计算学习进度（假设每个级别需要60小时练习，当前级别已完成的百分比）
        hours_needed_per_level = 60
        progress_percentage = min(100, (student.total_practice_time / hours_needed_per_level) * 100)
        student.progress = round(progress_percentage, 1)
    
    context = {
        'teacher': teacher,  # 添加教师信息到上下文
        'students': students,
        'total_students': total_students,
        'new_students_this_month': new_students_this_month,
        'level_distribution': level_distribution,
        'recent_students': recent_students,
        'search_query': search_query,
        'unread_notifications_count': 0,  # 为模板提供默认值
        'attendance_rate': round(today_attendance_rate, 1),  # 使用今日出勤率，并保留一位小数
        'today_attendance': today_attendance  # 添加真实的今日练琴人数
    }
    
    return render(request, 'teachers/teacher_students.html', context)


@login_required
@teacher_required
def student_detail(request, student_id):
    """学生详情 - 重定向到学生列表页面并打开详情模态框"""
    # 由于现在使用模态框展示详情，这里只需要重定向到学生列表页面
    # 将student_id作为URL参数，以便前端页面加载后自动打开对应的模态框
    return redirect(f"{reverse('teachers:students')}?view_student={student_id}")


@login_required
@teacher_required
def add_student(request):
    """添加学生"""
    if request.method == 'POST':
        # 处理表单提交
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        parent_phone = request.POST.get('parent_phone')
        parent_name = request.POST.get('parent_name', '')
        school = request.POST.get('school', '')
        level_id = request.POST.get('level')
        target_level_id = request.POST.get('target_level', level_id)
        
        # 创建学生记录
        student = Student(
            name=name,
            phone=phone,
            parent_phone=parent_phone,
            parent_name=parent_name,
            school=school
        )
        
        # 设置级别
        if level_id:
            piano_level = get_object_or_404(PianoLevel, id=level_id)
            student.level = piano_level.level
            
        if target_level_id:
            piano_target_level = get_object_or_404(PianoLevel, id=target_level_id)
            student.target_level = piano_target_level.level
        else:
            student.target_level = student.level
            
        # 创建用户账号
        from django.contrib.auth.models import User
        import random
        username = f"student_{random.randint(10000, 99999)}"
        password = f"pwd_{random.randint(100000, 999999)}"
        user = User.objects.create_user(username=username, password=password)
        student.user = user
            
        student.save()
        
        # 将学生添加到教师的某门课程已通过信号自动处理
        messages.success(request, f'学生"{name}"已成功添加，账号：{username}，密码：{password}')
        return redirect('teachers:students')
        
    # GET请求，显示添加学生表单
    piano_levels = PianoLevel.objects.all()
    return render(request, 'teachers/add_student.html', {'piano_levels': piano_levels})


@login_required
@teacher_required
def edit_student(request, student_id):
    """编辑学生信息"""
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, id=student_id)
    
    # 确认该学生是否与教师相关
    is_related = Course.objects.filter(
        teacher=teacher,
        students=student,
        is_active=True
    ).exists()
    
    if not is_related:
        messages.error(request, '您无权编辑此学生信息')
        return redirect('teachers:students')
    
    if request.method == 'POST':
        # 处理表单提交
        student.name = request.POST.get('name', student.name)
        student.phone = request.POST.get('phone', student.phone)
        student.parent_phone = request.POST.get('parent_phone', student.parent_phone)
        student.parent_name = request.POST.get('parent_name', student.parent_name)
        student.school = request.POST.get('school', student.school)
        
        # 获取并处理性别信息
        gender = request.POST.get('gender')
        if gender in ['male', 'female']:
            student.gender = gender
            
        # 处理级别信息
        level = request.POST.get('level')
        if level and level.isdigit():
            student.level = int(level)
            
        target_level = request.POST.get('target_level')
        if target_level and target_level.isdigit():
            student.target_level = int(target_level)
            
        student.save()
        
        # 使用会话变量而不是消息框架保存学生信息更新的消息
        # 这样消息只会在学生管理页面显示，不会影响考勤记录界面
        request.session['student_updated'] = {
            'name': student.name,
            'timestamp': str(timezone.now())
        }
        
        # AJAX请求返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'学生"{student.name}"信息已更新'
            })
        
        return redirect('teachers:students')
    
    # 对于GET请求，重定向到学生列表页面并打开编辑模态框
    return redirect(f"{reverse('teachers:students')}?edit_student={student_id}")


@login_required
@teacher_required
def delete_student(request, student_id):
    """删除学生"""
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, id=student_id)
    
    # 确认该学生是否与教师相关
    is_related = Course.objects.filter(
        teacher=teacher,
        students=student,
        is_active=True
    ).exists()
    
    if not is_related:
        messages.error(request, '您无权删除此学生')
        return redirect('teachers:students')
    
    if request.method == 'POST':
        # 实际上我们只是将学生与教师课程的关系解除
        courses = Course.objects.filter(
            teacher=teacher,
            students=student,
            is_active=True
        )
        
        for course in courses:
            course.students.remove(student)
        
        messages.success(request, f'学生"{student.name}"已从您的学生列表中移除')
    
    return redirect('teachers:students')


@login_required
@teacher_required
def teacher_courses(request):
    """教师的课程列表 - 重定向到练琴安排"""
    return redirect('teachers:piano_arrangement')


@login_required
@teacher_required
def course_detail(request, course_id):
    """课程详情 - 重定向到练琴安排"""
    return redirect('teachers:piano_arrangement')


@login_required
@teacher_required
def add_course(request):
    """添加课程 - 重定向到练琴安排"""
    return redirect('teachers:piano_arrangement')


@login_required
@teacher_required
def edit_course(request, course_id):
    """编辑课程 - 重定向到练琴安排"""
    return redirect('teachers:piano_arrangement')


@login_required
@teacher_required
def teacher_attendance(request):
    """教师考勤记录"""
    teacher = request.user.teacher_profile
    
    # 自动关闭过期的考勤会话
    expired_sessions_count = AttendanceSession.check_and_close_expired_sessions()
    if expired_sessions_count > 0:
        messages.info(request, f'已自动关闭 {expired_sessions_count} 个过期的考勤会话')
    
    # 获取当前时间
    current_time = timezone.now()
    
    # 设置今日日期变量（确保在整个函数中可用）
    today = current_time.date()
    today_str = today.strftime('%Y-%m-%d')
    
    # 获取今日考勤会话
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    # 获取本周开始和结束时间
    week_start = today_start - timedelta(days=current_time.weekday())
    week_end = week_start + timedelta(days=7) - timedelta(seconds=1)
    
    # 获取本月开始和结束时间
    month_start = today_start.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year+1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month+1) - timedelta(days=1)
    month_end = month_end.replace(hour=23, minute=59, second=59)
    
    # 获取活跃的考勤会话
    active_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        status='active'
    ).order_by('-start_time')
    
    # 获取最近的考勤会话，确保活跃会话显示在前面
    all_recent_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher
    ).order_by('-start_time')

    # 先获取活跃会话，然后获取非活跃的最近会话，合并为一个列表
    active_recent = list(all_recent_sessions.filter(status='active'))
    closed_recent = list(all_recent_sessions.filter(status='closed'))[:10-len(active_recent)]
    recent_sessions = active_recent + closed_recent
    
    # 确保不超过10条记录
    if len(recent_sessions) > 10:
        recent_sessions = recent_sessions[:10]
    
    # 为每个会话计算实际出勤人数和总学生数
    attendance_data = {}
    for session in recent_sessions:
        if session.course:
            total_students_count = session.course.students.count()
            attendance_count = AttendanceRecord.objects.filter(session=session).count()
            # 将这些数据存储在字典中
            attendance_data[session.id] = {
                'total_students_count': total_students_count,
                'attendance_count': attendance_count
            }
            # 使用自定义属性名称避免与模型属性冲突
            session.actual_attendance_count = attendance_count
            session.actual_total_students_count = total_students_count
        else:
            attendance_data[session.id] = {
                'total_students_count': 0,
                'attendance_count': 0
            }
            # 使用自定义属性名称避免与模型属性冲突
            session.actual_attendance_count = 0
            session.actual_total_students_count = 0
    
    # 检查URL中是否有qrcode参数
    qrcode_uuid = request.GET.get('qrcode')
    session_id = request.GET.get('session_id')
    qrcode_to_display = None
    
    # 如果有会话ID，确保它在最近会话列表中的第一位
    if session_id:
        try:
            session = AttendanceSession.objects.get(id=session_id, course__teacher=teacher)
            # 如果在近期会话列表中找到该会话，将其移到列表首位
            if session in recent_sessions:
                recent_sessions.remove(session)
            recent_sessions.insert(0, session)
            
            # 如果该会话有关联的二维码，显示它
            if hasattr(session, 'qrcode') and session.qrcode:
                qrcode_to_display = session.qrcode
        except AttendanceSession.DoesNotExist:
            pass
    
    if qrcode_uuid and not qrcode_to_display:
        try:
            qrcode_to_display = QRCode.objects.get(code=qrcode_uuid)
        except QRCode.DoesNotExist:
            pass
    
    # 如果没有指定的二维码，尝试获取最新的活跃二维码
    if not qrcode_to_display and active_sessions.exists():
        active_session = active_sessions.first()
        if hasattr(active_session, 'qrcode') and active_session.qrcode:
            qrcode_to_display = active_session.qrcode
    
    # 定义二维码URL变量，避免未定义错误
    qrcode_url = None
    if qrcode_to_display and qrcode_to_display.qr_code_image:
        qrcode_url = qrcode_to_display.qr_code_image.url

    # 统计今日出勤率
    today_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        start_time__gte=today_start
    )
    today_total_students = 0
    today_attended_students = 0
    
    for session in today_sessions:
        enrolled_students = session.course.students.count()
        today_total_students += enrolled_students
        attended = AttendanceRecord.objects.filter(session=session).count()
        today_attended_students += attended
    
    # 获取PracticeRecord中今日练琴的非重复学生
    practice_student_ids = set(PracticeRecord.objects.filter(
        date=today,
        student__courses__teacher=teacher
    ).values_list('student_id', flat=True).distinct())
    
    # 获取AttendanceRecord中今日签到的非重复学生
    attendance_student_ids = set(AttendanceRecord.objects.filter(
        check_in_time__date=today,
        session__course__teacher=teacher
    ).values_list('student_id', flat=True).distinct())
    
    # 合并两类记录中的学生ID
    all_attended_student_ids = attendance_student_ids.union(practice_student_ids)
    
    # 计算今日总出勤人数（去重后）
    today_total_attended = len(all_attended_student_ids)
    
    # 获取总学生数（所有课程的学生，不重复计算）
    all_students_count = Student.objects.filter(
        courses__teacher=teacher
    ).distinct().count()
    
    # 重新计算今日出勤率
    today_attendance_rate = 0
    if all_students_count > 0:
        today_attendance_rate = (today_total_attended / all_students_count) * 100
    
    # 计算周出勤率 - 使用类似逻辑
    # 获取本周PracticeRecord签到的非重复学生
    practice_weekly_student_ids = set(PracticeRecord.objects.filter(
        date__gte=week_start.date(),
        date__lte=week_end.date(),
        student__courses__teacher=teacher
    ).values_list('student_id', flat=True).distinct())
    
    # 获取本周AttendanceRecord签到的非重复学生
    attendance_weekly_student_ids = set(AttendanceRecord.objects.filter(
        check_in_time__gte=week_start,
        check_in_time__lte=week_end,
        session__course__teacher=teacher
    ).values_list('student_id', flat=True).distinct())
    
    # 合并两类记录
    all_weekly_attended_ids = attendance_weekly_student_ids.union(practice_weekly_student_ids)
    
    # 计算每个学生本周应该上的课程次数
    # 对于每个学生，获取他们本周的课程安排
    from django.db.models import Q
    
    # 获取本周内所有课程安排，用于计算应出勤总次数
    weekday_list = [(week_start + timedelta(days=i)).weekday() for i in range(7)]
    active_students = Student.objects.filter(courses__teacher=teacher).distinct()
    
    # 统计每个学生在本周的总课程数
    total_courses_in_week = 0
    total_attended_in_week = 0
    
    for student in active_students:
        # 获取该学生本周的课程安排
        student_courses = student.courses.filter(teacher=teacher)
        # 计算该学生在本周的课程数
        student_schedules = CourseSchedule.objects.filter(
            course__in=student_courses, 
            weekday__in=weekday_list,
            is_active=True
        ).count()
        
        # 累加总课程数
        total_courses_in_week += student_schedules
        
        # 如果学生有考勤记录，计入已出勤次数
        if student.id in all_weekly_attended_ids:
            # 计算该学生本周实际出勤次数
            attended_records = AttendanceRecord.objects.filter(
                student=student,
                check_in_time__gte=week_start,
                check_in_time__lte=week_end,
                session__course__teacher=teacher
            ).count()
            
            # 计入总出勤次数
            total_attended_in_week += attended_records if attended_records > 0 else 1
    
    # 计算周出勤率 - 实际出勤次数除以应出勤次数
    weekly_attendance_rate = 0
    if total_courses_in_week > 0:
        weekly_attendance_rate = (total_attended_in_week / total_courses_in_week) * 100
    # 限制最大值为100%
    weekly_attendance_rate = min(weekly_attendance_rate, 100)
    
    print(f"DEBUG - 本周总课程数: {total_courses_in_week}")
    print(f"DEBUG - 本周总出勤次数: {total_attended_in_week}")
    print(f"DEBUG - 本周出勤率: {weekly_attendance_rate}%")
    
    # 计算月出勤率 - 使用类似的更准确的逻辑
    # 获取本月PracticeRecord签到的非重复学生
    practice_monthly_student_ids = set(PracticeRecord.objects.filter(
        date__gte=month_start.date(),
        date__lte=month_end.date(),
        student__courses__teacher=teacher
    ).values_list('student_id', flat=True).distinct())
    
    # 获取本月AttendanceRecord签到的非重复学生
    attendance_monthly_student_ids = set(AttendanceRecord.objects.filter(
        check_in_time__gte=month_start,
        check_in_time__lte=month_end,
        session__course__teacher=teacher
    ).values_list('student_id', flat=True).distinct())
    
    # 合并两类记录
    all_monthly_attended_ids = attendance_monthly_student_ids.union(practice_monthly_student_ids)
    
    # 获取本月天数
    month_days = (month_end.date() - month_start.date()).days + 1
    month_weekday_list = [(month_start + timedelta(days=i)).weekday() for i in range(month_days)]
    
    # 统计每个学生在本月的总课程数
    total_courses_in_month = 0
    total_attended_in_month = 0
    
    for student in active_students:
        # 获取该学生本月的课程安排
        student_courses = student.courses.filter(teacher=teacher)
        # 计算该学生在本月的课程数
        student_schedules = 0
        
        # 对于每个课程，统计每周的排课
        for course in student_courses:
            # 获取课程每周排课
            schedules = CourseSchedule.objects.filter(
                course=course,
                weekday__in=month_weekday_list,
                is_active=True
            )
            
            # 统计本月该课程的排课次数
            for schedule in schedules:
                # 计算该排课在本月出现的次数
                occurrences = len([day for day in range(month_days) 
                               if (month_start + timedelta(days=day)).weekday() == schedule.weekday])
                student_schedules += occurrences
        
        # 累加总课程数
        total_courses_in_month += student_schedules
        
        # 如果学生有考勤记录，计入已出勤次数
        if student.id in all_monthly_attended_ids:
            # 计算该学生本月实际出勤次数
            attended_records = AttendanceRecord.objects.filter(
                student=student,
                check_in_time__gte=month_start,
                check_in_time__lte=month_end,
                session__course__teacher=teacher
            ).count()
            
            # 计入总出勤次数
            total_attended_in_month += attended_records
    
    # 计算月出勤率 - 实际出勤次数除以应出勤次数
    monthly_attendance_rate = 0
    if total_courses_in_month > 0:
        monthly_attendance_rate = (total_attended_in_month / total_courses_in_month) * 100
    # 限制最大值为100%
    monthly_attendance_rate = min(monthly_attendance_rate, 100)
    
    print(f"DEBUG - 本月总课程数: {total_courses_in_month}")
    print(f"DEBUG - 本月总出勤次数: {total_attended_in_month}")
    print(f"DEBUG - 本月出勤率: {monthly_attendance_rate}%")
    
    # 练琴时长统计 - 只统计教师自己课程的学生
    # 获取教师课程的所有学生ID
    teacher_student_ids = Student.objects.filter(
        courses__teacher=teacher
    ).values_list('id', flat=True).distinct()
    
    today_practice_time = PracticeRecord.objects.filter(
        student_id__in=teacher_student_ids,
        start_time__gte=today_start
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    weekly_practice_time = PracticeRecord.objects.filter(
        student_id__in=teacher_student_ids,
        start_time__gte=week_start
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    monthly_practice_time = PracticeRecord.objects.filter(
        student_id__in=teacher_student_ids,
        start_time__gte=month_start
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    # 记录练琴记录数量，用于调试
    weekly_practice_count = PracticeRecord.objects.filter(
        student_id__in=teacher_student_ids,
        start_time__gte=week_start
    ).count()
    
    print(f"DEBUG - 教师学生总数: {len(teacher_student_ids)}")
    print(f"DEBUG - 本周练琴记录数: {weekly_practice_count}")
    print(f"DEBUG - 本周总练琴时长(分钟): {weekly_practice_time}")
    
    # 转换为小时
    today_practice_time = today_practice_time / 60  # 假设duration存储的是分钟
    weekly_practice_time = weekly_practice_time / 60
    monthly_practice_time = monthly_practice_time / 60
    
    # 计算练琴时长百分比（为了进度条）
    max_practice_time = 10  # 假设10小时为100%
    today_practice_percentage = min((today_practice_time / max_practice_time) * 100, 100)
    weekly_practice_percentage = min((weekly_practice_time / (max_practice_time * 7)) * 100, 100)
    monthly_practice_percentage = min((monthly_practice_time / (max_practice_time * 30)) * 100, 100)
    
    # 获取教师的课程列表（用于生成考勤码表单）
    courses = Course.objects.filter(teacher=teacher)
    
    # 获取总学生数
    total_students = Student.objects.filter(courses__teacher=teacher).distinct().count()
    
    # 获取所有学生（用于手动添加考勤）
    all_students = Student.objects.filter(courses__teacher=teacher).distinct().order_by('name')
    
    # 今日考勤人数
    # today = current_time.date()  # 删除这行，因为already定义
    # today_str = today.strftime('%Y-%m-%d')  # 删除这行，因为already定义
    
    # 使用原始SQL查询获取AttendanceRecord考勤人数
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT ar.student_id) 
            FROM attendance_attendancerecord ar
            JOIN attendance_attendancesession ats ON ar.session_id = ats.id
            JOIN courses_course cc ON ats.course_id = cc.id
            WHERE DATE(ar.check_in_time) = %s
        """, [today_str])
        attendance_today_ar = cursor.fetchone()[0]
    
    # 使用ORM查询获取PracticeRecord练琴人数
    practice_today = PracticeRecord.objects.filter(
        date=today
    ).values('student').distinct().count()
    
    # 合并两种记录获取总到课人数（需要去重）
    attendance_student_ids = set()
    
    # 获取AttendanceRecord中的学生ID
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT ar.student_id 
            FROM attendance_attendancerecord ar
            WHERE DATE(ar.check_in_time) = %s
        """, [today_str])
        for row in cursor.fetchall():
            attendance_student_ids.add(row[0])
    
    # 获取PracticeRecord中的学生ID
    practice_student_ids = PracticeRecord.objects.filter(
        date=today
    ).values_list('student_id', flat=True).distinct()
    
    # 合并并去重
    for student_id in practice_student_ids:
        attendance_student_ids.add(student_id)
    
    # 总到课人数
    attendance_today = len(attendance_student_ids)
    
    print(f"DEBUG - 今日日期: {today}")
    print(f"DEBUG - AttendanceRecord考勤人数: {attendance_today_ar}")
    print(f"DEBUG - PracticeRecord练琴人数: {practice_today}")
    print(f"DEBUG - 合并去重后总到课人数: {attendance_today}")
    
    context = {
        'teacher': teacher,
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
        'qrcode_to_display': qrcode_to_display,
        'qrcode_url': qrcode_url,
        'today_attendance_rate': today_attendance_rate,
        'weekly_attendance_rate': weekly_attendance_rate,
        'monthly_attendance_rate': monthly_attendance_rate,
        'today_practice_time': today_practice_time,
        'today_practice_percentage': today_practice_percentage,
        'weekly_practice_time': weekly_practice_time,
        'weekly_practice_percentage': weekly_practice_percentage,
        'monthly_practice_time': monthly_practice_time,
        'monthly_practice_percentage': monthly_practice_percentage,
        'attendance_data': attendance_data,  # 添加出勤数据字典到上下文
        'courses': courses,  # 添加课程列表
        'total_students': total_students,  # 添加总学生数
        'all_students': all_students,  # 添加所有学生
        'attendance_today': attendance_today  # 添加今日考勤人数
    }
    
    return render(request, 'teachers/teacher_attendance.html', context)


@login_required
@teacher_required
def generate_qrcode(request):
    """生成考勤二维码"""
    teacher = request.user.teacher_profile
    
    # 处理GET请求 - 直接生成默认考勤码
    if request.method == 'GET':
        try:
            # 获取当前时间和过期时间(默认24小时)
            current_time = timezone.now()
            expires_at = current_time + timezone.timedelta(hours=24)
            
            # 关闭该教师的所有活跃会话
            active_sessions = AttendanceSession.objects.filter(
                course__teacher=teacher,
                status='active'
            )
            for session in active_sessions:
                session.status = 'closed'
                session.end_time = current_time
                session.save()
            
            # 创建或获取通用考勤课程
            default_course, created = Course.objects.get_or_create(
                name="通用考勤",
                code="DEFAULT",
                teacher=teacher,
                defaults={
                    'description': '自动生成的通用考勤课程',
                    'level': PianoLevel.objects.first()  # 使用第一个级别作为默认值
                }
            )
            
            # 创建二维码
            import uuid
            qrcode_uuid = str(uuid.uuid4())
            qrcode = QRCode.objects.create(
                course=default_course,
                uuid=uuid.UUID(qrcode_uuid),
                code=qrcode_uuid,
                expires_at=expires_at
            )
            
            # 创建考勤会话
            # 获取或创建一个当天的课程安排
            weekday = current_time.weekday()
            schedule, created = CourseSchedule.objects.get_or_create(
                course=default_course,
                weekday=weekday,
                defaults={
                    'start_time': current_time.time(),
                    'end_time': expires_at.time(),
                    'is_temporary': True
                }
            )
            
            # 创建考勤会话
            session = AttendanceSession.objects.create(
                course=default_course,
                schedule=schedule,
                qrcode=qrcode,
                created_by=request.user,
                start_time=current_time,
                end_time=expires_at,
                description=f"自动生成的考勤 - {current_time.strftime('%Y-%m-%d %H:%M')}",
                status='active'
            )
            
            # 重定向到考勤页面，并显示二维码
            messages.success(request, '考勤二维码已生成')
            return redirect(f'/teachers/attendance/?qrcode={qrcode_uuid}&session_id={session.id}')
            
            
        except Exception as e:
            messages.error(request, f'生成二维码时发生错误：{str(e)}')
            return redirect('teachers:attendance')
    
    # 处理POST请求
    if request.method == 'POST':
        # 处理来自考勤页面的请求
        course_id = request.POST.get('course_id')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        description = request.POST.get('description', '')
        
        # 获取课程
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        # 解析时间
        today = timezone.now().date()
        hours, minutes = map(int, start_time_str.split(':'))
        start_time = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=hours, minute=minutes)))
        
        hours, minutes = map(int, end_time_str.split(':'))
        end_time = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=hours, minute=minutes)))
        
        # 确保结束时间不超过24小时
        max_end_time = start_time + timezone.timedelta(hours=24)
        if end_time > max_end_time:
            end_time = max_end_time
        
        # 关闭该教师的所有活跃会话
        active_sessions = AttendanceSession.objects.filter(
            course__teacher=teacher,
            status='active'
        )
        for session in active_sessions:
            session.status = 'closed'
            session.end_time = timezone.now()
            session.save()
        
        # 获取或创建课程安排
        from django.db.models import Q
        # 当前是周几（0-6，周一为0）
        weekday = timezone.now().weekday()
        
        # 查找匹配的课程安排
        schedule = CourseSchedule.objects.filter(
            Q(course=course) & 
            Q(weekday=weekday) & 
            Q(start_time__hour=start_time.hour, start_time__minute=start_time.minute) & 
            Q(end_time__hour=end_time.hour, end_time__minute=end_time.minute)
        ).first()
        
        # 如果没有找到匹配的课程安排，则创建一个临时的
        if not schedule:
            schedule = CourseSchedule.objects.create(
                course=course,
                weekday=weekday,
                start_time=start_time.time(),
                end_time=end_time.time(),
                is_temporary=True
            )
        
        # 创建二维码
        import uuid
        qrcode_uuid = str(uuid.uuid4())
        qrcode = QRCode.objects.create(
            course=course,
            uuid=uuid.UUID(qrcode_uuid),
            code=qrcode_uuid,  # 保持兼容性，同时设置code字段
            expires_at=end_time
        )
        
        # 创建考勤会话
        session = AttendanceSession.objects.create(
            course=course,
            schedule=schedule,
            qrcode=qrcode,  # 设置二维码关联
            created_by=request.user,
            start_time=start_time,
            end_time=end_time,
            description=description,
            status='active'
        )
        
        # 重定向到考勤页面，并显示二维码
        messages.success(request, '考勤二维码已生成')
        return redirect(f'/teachers/attendance/?qrcode={qrcode_uuid}&session_id={session.id}')
    
    return redirect('teachers:attendance')


@login_required
@teacher_required
def attendance_session_detail(request, session_id):
    """考勤会话详情"""
    # 每次访问都强制从数据库重新获取会话数据
    session = get_object_or_404(AttendanceSession.objects.select_related('course'), id=session_id)
    
    # 权限检查
    if session.course.teacher != request.user.teacher_profile and session.created_by != request.user:
        messages.error(request, "没有权限查看此考勤记录")
        return redirect('teachers:attendance')
    
    # 实时获取考勤记录，不使用缓存
    records = AttendanceRecord.objects.filter(session=session).select_related('student').order_by('student__name')
    
    # 获取未签到学生列表
    attended_student_ids = records.values_list('student_id', flat=True)
    all_students = session.course.students.all()
    absent_students = all_students.exclude(id__in=attended_student_ids)
    
    # 计算出勤率
    attendance_rate = 0
    if all_students.count() > 0:
        attendance_rate = int(records.count() / all_students.count() * 100)
    
    # 处理本地时间显示和时长计算
    current_time = timezone.localtime(timezone.now())
    
    # 计算每个学生的练习时长总和（来自PracticeRecord而不是AttendanceRecord）
    from mymanage.students.models import PracticeRecord
    from django.db.models import Sum
    
    for record in records:
        # 获取学生的所有练习记录，并计算总时长
        total_practice_time = PracticeRecord.objects.filter(
            student=record.student
        ).aggregate(total=Sum('duration'))['total'] or 0
        
        # 将总时长添加到记录对象上（不存储到数据库）
        record.total_practice_time = total_practice_time
        
        # 转换为本地时间
        record.check_in_local = timezone.localtime(record.check_in_time)
        
        # 计算持续时间
        if record.check_out_time:
            record.check_out_local = timezone.localtime(record.check_out_time)
            
            # 检测并修复异常时间
            if record.check_out_local < record.check_in_local:
                record.duration_minutes = 30  # 设置一个默认值
            else:
                time_diff = record.check_out_local - record.check_in_local
                minutes = time_diff.total_seconds() / 60
                
                # 限制最大持续时间为4小时
                if minutes > 240:
                    record.duration_minutes = 240
                else:
                    record.duration_minutes = minutes
        else:
            # 如果未签退，计算从签到到当前的时间
            time_diff = current_time - record.check_in_local
            minutes = time_diff.total_seconds() / 60
            
            # 限制合理范围
            if minutes < 0:
                record.duration_minutes = 0
            elif minutes > 240:
                record.duration_minutes = 240
            else:
                record.duration_minutes = minutes
    
    context = {
        'session': session,
        'records': records,
        'absent_students': absent_students,
        'attendance_rate': attendance_rate,
    }
    
    return render(request, 'teachers/attendance_session_detail.html', context)


@login_required
@teacher_required
def attendance_stats(request):
    """考勤统计"""
    teacher = request.user.teacher_profile
    
    # 获取过滤参数
    course_id = request.GET.get('course_id')
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    # 构建基本查询
    attendance_records = AttendanceRecord.objects.filter(session__course__teacher=teacher)
    
    # 导入PracticeRecord模型
    from mymanage.students.models import PracticeRecord
    practice_records = PracticeRecord.objects.filter(student__courses__teacher=teacher)
    
    # 应用过滤条件
    if course_id:
        attendance_records = attendance_records.filter(session__course_id=course_id)
        practice_records = practice_records.filter(student__courses__id=course_id)
    
    if month and year:
        attendance_records = attendance_records.filter(
            check_in_time__month=month,
            check_in_time__year=year
        )
        practice_records = practice_records.filter(
            date__month=month,
            date__year=year
        )
    
    # 准备合并结果的字典
    student_stats_dict = {}
    
    # 处理AttendanceRecord
    attendance_stats = attendance_records.values('student__id', 'student__name').annotate(
        count=Count('id'),
        total_hours=Sum('duration')
    )
    
    # 添加到字典
    for stat in attendance_stats:
        student_id = stat['student__id']
        if student_id not in student_stats_dict:
            student_stats_dict[student_id] = {
                'student__name': stat['student__name'],
                'count': stat['count'],
                'total_hours': stat['total_hours'] or 0
            }
        else:
            student_stats_dict[student_id]['count'] += stat['count']
            student_stats_dict[student_id]['total_hours'] += (stat['total_hours'] or 0)
    
    # 处理PracticeRecord
    practice_stats = practice_records.values('student__id', 'student__name').annotate(
        count=Count('id'),
        total_minutes=Sum('duration')
    )
    
    # 添加到字典 - 注意PracticeRecord的时长是分钟，需要转换为小时
    for stat in practice_stats:
        student_id = stat['student__id']
        total_hours = (stat['total_minutes'] or 0) / 60.0  # 转换为小时
        
        if student_id not in student_stats_dict:
            student_stats_dict[student_id] = {
                'student__name': stat['student__name'],
                'count': stat['count'],
                'total_hours': total_hours
            }
        else:
            student_stats_dict[student_id]['count'] += stat['count']
            student_stats_dict[student_id]['total_hours'] += total_hours
    
    # 转换回列表形式
    student_stats = [
        {
            'student__name': data['student__name'],
            'count': data['count'],
            'total_hours': round(data['total_hours'], 1)  # 四舍五入到一位小数
        }
        for student_id, data in student_stats_dict.items()
    ]
    
    # 获取教师的所有课程（用于过滤）
    courses = Course.objects.filter(teacher=teacher)
    
    context = {
        'student_stats': student_stats,
        'courses': courses,
        'selected_course_id': course_id,
        'selected_month': month,
        'selected_year': year
    }
    
    return render(request, 'teachers/attendance_stats.html', context)


@login_required
@teacher_required
def teacher_sheet_music(request):
    """教师曲谱管理"""
    teacher = request.user.teacher_profile
    
    # 获取所有曲谱
    sheet_music_list = SheetMusic.objects.all()
    
    # 获取过滤参数
    difficulty = request.GET.get('difficulty')
    style = request.GET.get('style')
    period = request.GET.get('period')
    search = request.GET.get('search')
    
    # 根据参数过滤
    if difficulty:
        sheet_music_list = sheet_music_list.filter(difficulty=difficulty)
    if style:
        sheet_music_list = sheet_music_list.filter(style=style)
    if period:
        sheet_music_list = sheet_music_list.filter(period=period)
    if search:
        sheet_music_list = sheet_music_list.filter(
            Q(title__icontains=search) | 
            Q(composer__icontains=search) |
            Q(description__icontains=search)
        )
    
    # 分页
    paginator = Paginator(sheet_music_list, 12)  # 每页显示12项
    page = request.GET.get('page')
    
    try:
        sheet_music = paginator.page(page)
    except PageNotAnInteger:
        # 如果页码不是整数，返回第一页
        sheet_music = paginator.page(1)
    except EmptyPage:
        # 如果页码超过了最大页数，返回最后一页
        sheet_music = paginator.page(paginator.num_pages)
    
    context = {
        'teacher': teacher,
        'sheet_music': sheet_music,
        'page_obj': sheet_music,
        'is_paginated': sheet_music.has_other_pages() if hasattr(sheet_music, 'has_other_pages') else True,
        'current_time': timezone.now(),
        'unread_notifications_count': 0,  # 为模板提供默认值
    }
    
    return render(request, 'teachers/teacher_sheet_music.html', context)


@login_required
@teacher_required
def sheet_music_detail(request, sheet_id):
    """曲谱详情"""
    sheet = get_object_or_404(SheetMusic, id=sheet_id)
    
    # 检查权限
    if sheet.uploaded_by != request.user and not sheet.is_public:
        messages.error(request, '您没有权限查看此曲谱')
        return redirect('teacher_sheet_music')
    
    return render(request, 'teachers/sheet_music_detail.html', {'sheet': sheet})


@login_required
@teacher_required
def add_sheet_music(request):
    """添加曲谱"""
    if request.method == 'POST':
        title = request.POST.get('title')
        composer = request.POST.get('composer')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        
        # 使用默认级别（ID=1）
        from mymanage.courses.models import PianoLevel
        default_level = PianoLevel.objects.first()
        
        if not default_level:
            # 如果没有任何级别记录，创建一个默认级别
            default_level = PianoLevel.objects.create(level=1, description="默认级别")
        
        # 创建曲谱，使用默认级别
        sheet = SheetMusic(
            title=title,
            composer=composer,
            level=default_level,  # 直接使用对象，不是ID
            description=description,
            file=file,
            uploaded_by=request.user,
            is_public=True  # 默认设置为公开
        )
        
        # 添加其他字段
        sheet.difficulty = request.POST.get('difficulty', '中级')
        sheet.style = request.POST.get('style', '古典')
        sheet.period = request.POST.get('period', '古典主义')
        
        if 'cover_image' in request.FILES:
            sheet.cover_image = request.FILES['cover_image']
        
        sheet.save()
        messages.success(request, '曲谱添加成功')
        return redirect('teachers:sheet_music')
    
    # 获取所有钢琴等级（虽然现在不再需要选择）
    levels = PianoLevel.objects.all()
    return render(request, 'teachers/add_sheet_music.html', {
        'levels': levels
    })


@login_required
@teacher_required
def edit_sheet_music(request, sheet_id):
    """编辑曲谱"""
    sheet = get_object_or_404(SheetMusic, id=sheet_id, uploaded_by=request.user)
    
    # 获取所有钢琴等级
    levels = PianoLevel.objects.all()
    
    if request.method == 'POST':
        sheet.title = request.POST.get('title')
        sheet.composer = request.POST.get('composer')
        
        # 使用默认级别或用户选择的级别
        level_id = request.POST.get('level')
        if level_id:
            try:
                sheet.level = PianoLevel.objects.get(id=level_id)
            except PianoLevel.DoesNotExist:
                # 如果选择的级别不存在，使用默认级别
                sheet.level = PianoLevel.objects.first()
        else:
            # 如果没有选择级别，使用默认级别
            sheet.level = PianoLevel.objects.first()
            
        sheet.description = request.POST.get('description')
        sheet.is_public = True  # 默认设置为公开
        
        # 更新其他字段
        sheet.difficulty = request.POST.get('difficulty', '中级')
        sheet.style = request.POST.get('style', '古典')
        sheet.period = request.POST.get('period', '古典主义')
        
        if 'file' in request.FILES:
            sheet.file = request.FILES['file']
        
        if 'cover_image' in request.FILES:
            sheet.cover_image = request.FILES['cover_image']
        
        sheet.save()
        messages.success(request, '曲谱更新成功')
        return redirect('teachers:sheet_music_detail', sheet_id=sheet.id)
    
    return render(request, 'teachers/edit_sheet_music.html', {
        'sheet': sheet,
        'levels': levels
    })


@login_required
@teacher_required
def delete_sheet_music(request, sheet_id):
    """删除曲谱"""
    sheet = get_object_or_404(SheetMusic, id=sheet_id, uploaded_by=request.user)
    
    if request.method == 'POST':
        sheet.delete()
        messages.success(request, '曲谱已删除')
        return redirect('teachers:sheet_music')
    
    return render(request, 'teachers/delete_sheet_music.html', {'sheet': sheet})


@login_required
@teacher_required
def teacher_finance(request):
    """财务管理"""
    teacher = request.user.teacher_profile
    
    # 获取当前日期
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # 计算本月和上月的起止日期
    first_day_of_month = today.replace(day=1)
    last_month = (first_day_of_month - timezone.timedelta(days=1)).replace(day=1)
    
    # 获取本月收入
    month_payments = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        payment_date__year=current_year,
        payment_date__month=current_month
    )
    month_income = month_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取上月收入（比较数据）
    last_month_income = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        payment_date__year=last_month.year,
        payment_date__month=last_month.month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 计算同比变化
    month_change_percentage = 0
    if last_month_income > 0:
        month_change_percentage = ((month_income - last_month_income) / last_month_income) * 100
    
    # 获取年度收入
    year_income = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        payment_date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取待收款项
    pending_payments = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='pending'
    )
    total_pending = pending_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取最近10条付款记录
    recent_payments = Payment.objects.filter(
        student__courses__teacher=teacher
    ).order_by('-created_at')[:10]
    
    # 按类别统计收入数据（饼图）
    categories = PaymentCategory.objects.all()
    category_data = []
    
    # 生成分类数据（仅使用实际数据）
    for category in categories:
        category_total = Payment.objects.filter(
            student__courses__teacher=teacher,
            status='paid',
            category=category,
            payment_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # 即使金额为0也添加到分类数据中，以确保所有分类都显示
        category_data.append({
            'name': category.name,
            'value': float(category_total)
        })
    
    # 过滤掉金额为0的分类（可选，如果希望显示所有分类可以注释掉）
    category_data = [item for item in category_data if item['value'] > 0]
    
    # 确保JSON数据格式正确
    try:
        category_data_json = json.dumps(category_data, ensure_ascii=False)
        print(f"DEBUG: 分类数据 JSON: {category_data_json}")
    except Exception as e:
        print(f"ERROR: JSON序列化分类数据失败: {e}")
        category_data_json = '[]'  # 失败时提供默认空数组
    
    # 移除备用测试数据逻辑
    # 如果没有数据，显示空图表
    
    # 按月统计本年度收入（折线图）
    monthly_income_data = []
    month_names = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    
    # 生成月度数据（仅使用实际数据）
    for month in range(1, 13):
        monthly_total = Payment.objects.filter(
            student__courses__teacher=teacher,
            status='paid',
            payment_date__year=current_year,
            payment_date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_income_data.append({
            'month': month_names[month-1],
            'value': float(monthly_total)
        })
    
    # 移除测试数据逻辑
    
    # 按支付类型统计本月收入
    payment_by_category = []
    for category in categories:
        category_month_total = Payment.objects.filter(
            student__courses__teacher=teacher,
            status='paid',
            category=category,
            payment_date__year=current_year,
            payment_date__month=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # 移除测试数据逻辑，只使用真实数据
        if category_month_total > 0:
            payment_by_category.append({
                'category': category.name,
                'amount': float(category_month_total)
            })
    
    # 移除备用测试数据逻辑
    
    # 统计学生人数和已付款学生比例
    total_students = Student.objects.filter(courses__teacher=teacher).distinct().count()
    paid_students = Student.objects.filter(
        courses__teacher=teacher,
        payments__status='paid',
        payments__payment_date__year=current_year,
        payments__payment_date__month=current_month
    ).distinct().count()
    
    paid_percentage = 0
    if total_students > 0:
        paid_percentage = (paid_students / total_students) * 100
    
    # 为了兼容原有模板
    chart_labels = json.dumps([item['month'] for item in monthly_income_data])
    income_data = json.dumps([item['value'] for item in monthly_income_data])
    category_labels = json.dumps([item['name'] for item in category_data])
    category_data_values = json.dumps([item['value'] for item in category_data])
    
    context = {
        'teacher': teacher,
        'month_income': month_income,
        'year_income': year_income,
        'month_change_percentage': month_change_percentage,
        'total_pending': total_pending,
        'pending_payments': pending_payments,
        'recent_payments': recent_payments,
        'category_data': category_data_json,
        'monthly_income_data': json.dumps(monthly_income_data, ensure_ascii=False),
        'payment_by_category': payment_by_category,
        'total_students': total_students,
        'paid_students': paid_students,
        'paid_percentage': paid_percentage,
        'current_month': month_names[current_month-1],
        'current_year': current_year,
        'finance_module_url': reverse('finance:payment_list'),
        # 删除冲突的category_data字段，避免与上面的category_data_json冲突
        'chart_labels': chart_labels,
        'income_data': income_data,
        'category_labels': category_labels,
        'category_values': category_data_values,
        'selected_period': '当月',
        'unread_notifications_count': 0,
        # 添加原始数据用于调试
        'debug_categories': str(category_data),
        'debug_category_json': category_data_json,
        # 关闭调试模式
        'debug_mode': False,
    }
    
    return render(request, 'teachers/teacher_finance.html', context)


@login_required
@teacher_required
def teacher_payments(request):
    """付款记录列表"""
    teacher = request.user.teacher_profile
    
    # 获取过滤参数
    status = request.GET.get('status')
    category = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # 获取该教师学生的所有付款记录
    payments = Payment.objects.filter(
        student__courses__teacher=teacher
    ).order_by('-created_at')
    
    # 应用过滤条件
    if status:
        payments = payments.filter(status=status)
    
    if category:
        payments = payments.filter(category__id=category)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        payments = payments.filter(created_at__date__gte=start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        payments = payments.filter(created_at__date__lte=end_date)
    
    # 获取统计数据
    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    total_overdue = payments.filter(status='overdue').aggregate(total=Sum('amount'))['total'] or 0
    
    # 分页处理
    paginator = Paginator(payments, 20)  # 每页20条
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取付款类型选项
    payment_categories = PaymentCategory.objects.all()
    
    context = {
        'teacher': teacher,
        'payments': page_obj,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
        'payment_categories': payment_categories,
        'selected_status': status,
        'selected_category': category,
        'start_date': start_date,
        'end_date': end_date,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'page_obj': page_obj,
        'unread_notifications_count': 0,  # 为模板提供默认值
    }
    
    return render(request, 'teachers/teacher_payments.html', context)


@login_required
def update_profile_ajax(request):
    """AJAX更新个人信息"""
    if request.method == 'POST':
        teacher_profile = request.user.teacher_profile
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher_profile)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': '更新成功'})
        return JsonResponse({'status': 'error', 'message': '表单验证失败'})
    return JsonResponse({'status': 'error', 'message': '不支持的请求方法'})


@login_required
@teacher_required
def piano_arrangement(request):
    """练琴安排视图（替代课程管理）"""
    teacher = request.user.teacher_profile
    current_time = timezone.localtime(timezone.now())
    
    # 添加调试日志
    logger = logging.getLogger(__name__)
    logger.info(f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"当前教师: {teacher.name}")
    
    # 获取所有钢琴及其状态
    pianos = Piano.objects.all().order_by('number')
    logger.info(f"系统中钢琴数量: {pianos.count()}")
    
    # 获取所有活跃的PracticeRecord
    from mymanage.students.models import PracticeRecord
    active_practice_records = PracticeRecord.objects.filter(
        status='active',
        date=current_time.date()
    ).select_related('student')
    
    # 为每个钢琴添加当前使用学生信息
    for piano in pianos:
        # 先检查AttendanceRecord中的记录
        if piano.is_active and piano.is_occupied:
            # 查找当前使用此钢琴的学生
            current_record = AttendanceRecord.objects.filter(
                piano=piano,
                status='checked_in'
            ).order_by('-check_in_time').first()
            
            if current_record:
                piano.current_student = current_record.student
                piano.start_time = timezone.localtime(current_record.check_in_time)
                piano.end_time = piano.start_time + timedelta(minutes=30)  # 标准练习时长30分钟
                
                # 计算已练习时间，使用本地时间
                time_diff = current_time - piano.start_time
                practiced_minutes = int(time_diff.total_seconds() / 60)
                
                # 如果计算结果异常（负数或超大值），进行修正
                if practiced_minutes < 0:
                    practiced_minutes = 0
                    logger.warning(f"检测到异常练习时间计算: {piano.start_time} > {current_time}")
                elif practiced_minutes > 240:  # 超过4小时可能是异常
                    practiced_minutes = 240
                    logger.warning(f"检测到异常长练习时间: {practiced_minutes}分钟")
                
                piano.practiced_time = f"{practiced_minutes}分钟"
                logger.info(f"钢琴{piano.number}被{current_record.student.name}使用中，已练习{practiced_minutes}分钟")
            else:
                # 检查是否有PracticeRecord正在使用此钢琴
                practice_record = active_practice_records.filter(
                    piano_number=piano.number,
                ).first()
                
                if practice_record:
                    # 有PracticeRecord正在使用此钢琴
                    piano.current_student = practice_record.student
                    piano.start_time = timezone.localtime(practice_record.start_time)
                    piano.end_time = timezone.localtime(practice_record.end_time) if practice_record.end_time else (piano.start_time + timedelta(minutes=30))
                    
                    # 计算已练习时间
                    time_diff = current_time - piano.start_time
                    practiced_minutes = int(time_diff.total_seconds() / 60)
                    
                    # 修正异常值
                    if practiced_minutes < 0:
                        practiced_minutes = 0
                    elif practiced_minutes > 240:
                        practiced_minutes = 240
                    
                    piano.practiced_time = f"{practiced_minutes}分钟"
                    logger.info(f"钢琴{piano.number}被{practice_record.student.name}使用中 (PracticeRecord)，已练习{practiced_minutes}分钟")
                else:
                    # 这里是错误状态：钢琴标记为占用，但没有对应的考勤记录
                    logger.warning(f"警告: 钢琴{piano.number}标记为占用，但找不到对应的考勤记录")
                    # 修正钢琴状态
                    piano.is_occupied = False
                    piano.save()
        else:
            # 检查是否有PracticeRecord正在使用此钢琴，但钢琴状态未更新
            practice_record = active_practice_records.filter(
                piano_number=piano.number,
            ).first()
            
            if practice_record and piano.is_active and not piano.is_occupied:
                # 将钢琴状态更新为占用
                piano.is_occupied = True
                piano.save()
                
                # 更新钢琴信息
                piano.current_student = practice_record.student
                piano.start_time = timezone.localtime(practice_record.start_time)
                piano.end_time = timezone.localtime(practice_record.end_time) if practice_record.end_time else (piano.start_time + timedelta(minutes=30))
                
                # 计算已练习时间
                time_diff = current_time - piano.start_time
                practiced_minutes = int(time_diff.total_seconds() / 60)
                
                # 修正异常值
                if practiced_minutes < 0:
                    practiced_minutes = 0
                elif practiced_minutes > 240:
                    practiced_minutes = 240
                
                piano.practiced_time = f"{practiced_minutes}分钟"
                logger.info(f"更新钢琴{piano.number}状态为占用，被{practice_record.student.name}使用中")
            else:
                logger.info(f"钢琴{piano.number} - 状态: {'可用' if piano.is_active else '维护中'}，{'被占用' if piano.is_occupied else '空闲'}")
    
    # 获取当前等待队列中的学生
    waiting_students = []
    active_waiters = WaitingQueue.objects.filter(
        is_active=True,
        session__status='active'
    ).order_by('join_time')
    
    # 计算今天的开始和结束时间（使用本地时区）
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1) - timedelta(microseconds=1)
    
    logger.info(f"今日开始时间: {today_start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"今日结束时间: {today_end.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 统计今日签到人数 - 使用date比较而不是datetime比较
    checked_in_today = AttendanceRecord.objects.filter(
        check_in_time__date=current_time.date(),
        session__course__teacher=teacher
    ).values('student').distinct().count()
    
    # 同时统计PracticeRecord中的签到人数
    practice_checked_in = PracticeRecord.objects.filter(
        date=current_time.date()
    ).values('student').distinct().count()
    
    # 合并两个统计结果，因为可能有重复，所以需要获取所有学生ID然后去重
    attendance_student_ids = AttendanceRecord.objects.filter(
        check_in_time__date=current_time.date(),
        session__course__teacher=teacher
    ).values_list('student_id', flat=True)
    
    practice_student_ids = PracticeRecord.objects.filter(
        date=current_time.date()
    ).values_list('student_id', flat=True)
    
    # 合并两个查询集并去重
    all_student_ids = set(list(attendance_student_ids) + list(practice_student_ids))
    total_checked_in = len(all_student_ids)
    
    logger.info(f"等待队列学生数量: {active_waiters.count()}")
    logger.info(f"今日考勤记录签到学生数量: {checked_in_today}")
    logger.info(f"今日练琴记录学生数量: {practice_checked_in}")
    logger.info(f"今日总签到学生数量(去重): {total_checked_in}")
    
    for waiter in active_waiters:
        waiter_join_time = timezone.localtime(waiter.join_time)
        waiting_time = int((current_time - waiter_join_time).total_seconds() / 60)
        estimated_start = waiter_join_time + timedelta(minutes=waiter.estimated_wait_time)
        
        waiting_students.append({
            'id': waiter.student.id,
            'name': waiter.student.name,
            'level': waiter.student.get_level_display() if hasattr(waiter.student, 'get_level_display') else f"{waiter.student.level}级",
            'wait_time': waiting_time,
            'estimated_start_time': estimated_start,
        })
        logger.info(f"等待学生: {waiter.student.name}，等待时间: {waiting_time}分钟")
    
    # 获取可用钢琴列表（用于手动分配）
    available_pianos = Piano.objects.filter(is_active=True, is_occupied=False)
    
    # 获取今日签到记录和练习记录
    from mymanage.students.models import PracticeRecord
    
    # 合并两种记录
    all_today_records = []
    
    # 1. 获取考勤记录
    attendance_records = AttendanceRecord.objects.filter(
        check_in_time__date=current_time.date()
    ).select_related('student', 'piano', 'session').order_by('-check_in_time')
    
    # 2. 获取练琴记录
    practice_records = PracticeRecord.objects.filter(
        date=current_time.date()
    ).select_related('student').order_by('-start_time')
    
    # 合并记录
    for record in attendance_records:
        record.local_check_in = timezone.localtime(record.check_in_time)
        if record.check_out_time:
            record.local_check_out = timezone.localtime(record.check_out_time)
            # 计算持续时间（分钟）
            time_diff = record.local_check_out - record.local_check_in
            record.duration_mins = int(time_diff.total_seconds() / 60)
            
            # 修正异常持续时间
            if record.duration_mins < 0:
                record.duration_mins = 0
            elif record.duration_mins > 240:  # 超过4小时可能是异常
                record.duration_mins = 240
        else:
            # 如果尚未签退，计算到当前时间的持续时间
            time_diff = current_time - record.local_check_in
            record.duration_mins = int(time_diff.total_seconds() / 60)
            
            # 修正异常持续时间
            if record.duration_mins < 0:
                record.duration_mins = 0
            elif record.duration_mins > 240:
                record.duration_mins = 240
        
        all_today_records.append(record)
    
    for record in practice_records:
        # 避免添加重复记录 (已经在考勤记录中的)
        if any(r.student_id == record.student_id and abs((r.check_in_time - record.start_time).total_seconds()) < 300 for r in attendance_records):
            continue
            
        # 添加本地化时间
        record.local_check_in = timezone.localtime(record.start_time)
        # 不再赋值check_in_time属性，使用原始的start_time属性
        
        # 设置结束时间相关属性
        if record.end_time:
            record.local_check_out = timezone.localtime(record.end_time)
            # 同样不直接设置check_out_time
        
        # 确保钢琴编号存在
        if not hasattr(record, 'piano_number') or record.piano_number is None:
            # 没有钢琴编号，设置默认值
            record.piano_number = 1
            
        # 添加到记录列表
        all_today_records.append(record)
    
    # 按时间排序 - 使用更安全的方式获取排序键
    def get_sort_key(record):
        # 尝试获取开始时间，使用不同可能的字段名
        if hasattr(record, 'start_time') and record.start_time:
            return record.start_time
        elif hasattr(record, 'check_in_time') and record.check_in_time:
            # 如果是属性而不是字段，直接访问可能会出错
            try:
                return record.check_in_time
            except:
                pass
        # 默认返回当前时间作为后备选项
        return current_time
    
    # 使用自定义排序函数
    try:
        all_today_records.sort(key=get_sort_key, reverse=True)
    except Exception as e:
        logger.error(f"排序练琴记录时出错: {str(e)}")
        # 如果排序失败，尝试更简单的方法或保持原样
    
    logger.info(f"今日总记录数: {len(all_today_records)}")
    
    # 钢琴使用率
    total_pianos = Piano.objects.filter(is_active=True).count()
    occupied_pianos = Piano.objects.filter(is_active=True, is_occupied=True).count()
    piano_usage_rate = f"{int(occupied_pianos / total_pianos * 100)}%" if total_pianos > 0 else "0%"
    
    # 等待人数
    waiting_count = WaitingQueue.objects.filter(is_active=True).count()
    
    # 平均等待时间
    average_wait = WaitingQueue.objects.filter(
        is_active=False,
        join_time__date=current_time.date()
    ).aggregate(avg_time=Avg('estimated_wait_time'))
    avg_wait_time = f"{int(average_wait['avg_time'] or 0)}分钟"
    
    # 检查并自动签退超时的记录
    auto_checkout_threshold = current_time - timedelta(hours=4)  # 4小时自动签退
    overtime_records = AttendanceRecord.objects.filter(
        status='checked_in',
        check_in_time__lt=auto_checkout_threshold
    )
    
    for record in overtime_records:
        logger.warning(f"自动签退超时记录: {record.student.name} - 签到时间: {record.check_in_time}")
        try:
            record.check_out()
        except Exception as e:
            logger.error(f"自动签退失败: {str(e)}")
            # 直接强制签退
            record.status = 'checked_out'
            record.check_out_time = current_time
            record.duration = 4.0  # 4小时
            record.duration_minutes = 240  # 240分钟
            record.save()
        
        # 确保创建对应的PracticeRecord记录 - 添加此部分代码
        from mymanage.students.models import PracticeRecord
        try:
            # 检查是否已有练琴记录
            existing_practice = PracticeRecord.objects.filter(
                student=record.student,
                date=record.check_in_time.date(),
                start_time=record.check_in_time
            ).exists()
            
            if not existing_practice:
                # 为自动签退的记录创建练琴记录
                piano_number = 1  # 默认钢琴编号
                if record.piano and hasattr(record.piano, 'number'):
                    piano_number = record.piano.number
                
                PracticeRecord.objects.create(
                    student=record.student,
                    date=record.check_in_time.date(),
                    start_time=record.check_in_time,
                    end_time=record.check_out_time,
                    duration=240,  # 4小时（240分钟）
                    piano_number=piano_number,
                    status='completed',
                    attendance_session=record.session
                )
                logger.info(f"为自动签退的学生{record.student.name}创建了练琴记录")
        except Exception as e:
            logger.error(f"创建练琴记录失败: {str(e)}")
    
    context = {
        'teacher': teacher,
        'pianos': pianos,
        'waiting_students': waiting_students,
        'available_pianos': available_pianos,
        'today_records': all_today_records,
        'current_time': current_time,
        'checked_in_today': total_checked_in,  # 使用合并后的去重统计
        'piano_usage_rate': piano_usage_rate,
        'waiting_count': waiting_count,
        'avg_wait_time': avg_wait_time,
    }
    
    return render(request, 'teachers/piano_arrangement.html', context)


@login_required
@teacher_required
def refresh_piano_status(request):
    """刷新钢琴状态（AJAX）"""
    try:
        # 获取所有钢琴状态
        pianos = Piano.objects.all()
        current_time = timezone.now()
        
        # 导入所需模型
        from mymanage.students.models import PracticeRecord
        
        # 获取所有活跃的PracticeRecord
        active_practice_records = PracticeRecord.objects.filter(
            status='active',
            date=current_time.date()
        ).select_related('student')
        
        piano_data = []
        for piano in pianos:
            # 查找当前使用此钢琴的学生
            student_info = None
            if piano.is_active and piano.is_occupied:
                current_record = AttendanceRecord.objects.filter(
                    piano=piano,
                    status='checked_in'
                ).order_by('-check_in_time').first()
                
                if current_record:
                    # 计算已练习时间
                    practiced_minutes = int((current_time - current_record.check_in_time).total_seconds() / 60)
                    
                    student_info = {
                        'id': current_record.student.id,
                        'name': current_record.student.name,
                        'level': str(current_record.student.level),
                        'start_time': current_record.check_in_time.strftime('%H:%M'),
                        'practiced_time': f"{practiced_minutes}分钟",
                        'end_time': (current_record.check_in_time + timedelta(minutes=30)).strftime('%H:%M')
                    }
                else:
                    # 检查是否有PracticeRecord在使用此钢琴
                    practice_record = active_practice_records.filter(
                        piano_number=piano.number
                    ).order_by('-start_time').first()
                    
                    if practice_record:
                        # 计算已练习时间
                        practiced_minutes = int((current_time - practice_record.start_time).total_seconds() / 60)
                        
                        # 如果计算结果异常，进行修正
                        if practiced_minutes < 0:
                            practiced_minutes = 0
                        elif practiced_minutes > 240:  # 超过4小时可能是异常
                            practiced_minutes = 240
                        
                        student_info = {
                            'id': practice_record.student.id,
                            'name': practice_record.student.name,
                            'level': str(practice_record.student.level),
                            'start_time': practice_record.start_time.strftime('%H:%M'),
                            'practiced_time': f"{practiced_minutes}分钟",
                            'end_time': (practice_record.start_time + timedelta(minutes=30)).strftime('%H:%M')
                        }
                    else:
                        # 钢琴被标记为占用，但找不到使用记录，更新状态
                        piano.is_occupied = False
                        piano.save()
            else:
                # 检查是否有PracticeRecord正在使用该钢琴，但钢琴状态未更新
                practice_record = active_practice_records.filter(
                    piano_number=piano.number
                ).order_by('-start_time').first()
                
                if practice_record and piano.is_active and not piano.is_occupied:
                    # 更新钢琴状态
                    piano.is_occupied = True
                    piano.save()
                    
                    # 计算已练习时间
                    practiced_minutes = int((current_time - practice_record.start_time).total_seconds() / 60)
                    
                    # 如果计算结果异常，进行修正
                    if practiced_minutes < 0:
                        practiced_minutes = 0
                    elif practiced_minutes > 240:  # 超过4小时可能是异常
                        practiced_minutes = 240
                    
                    student_info = {
                        'id': practice_record.student.id,
                        'name': practice_record.student.name,
                        'level': str(practice_record.student.level),
                        'start_time': practice_record.start_time.strftime('%H:%M'),
                        'practiced_time': f"{practiced_minutes}分钟",
                        'end_time': (practice_record.start_time + timedelta(minutes=30)).strftime('%H:%M')
                    }
            
            piano_data.append({
                'id': piano.id,
                'number': piano.number,
                'brand': piano.brand,
                'model': piano.model,
                'is_active': piano.is_active,
                'is_occupied': piano.is_occupied,
                'student': student_info
            })
        
        return JsonResponse({
            'success': True,
            'pianos': piano_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@teacher_required
def assign_piano(request):
    """手动为学生分配钢琴"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法不允许'})
    
    student_id = request.POST.get('student_id')
    piano_id = request.POST.get('piano_id')
    
    if not student_id or not piano_id:
        return JsonResponse({'success': False, 'message': '缺少必要参数'})
    
    try:
        from mymanage.students.models import Student
        from mymanage.courses.models import Piano
        from mymanage.attendance.models import WaitingQueue, AttendanceSession
        
        student = Student.objects.get(id=student_id)
        piano = Piano.objects.get(id=piano_id)
        
        # 检查钢琴是否可用
        if not piano.is_active or piano.is_occupied:
            return JsonResponse({'success': False, 'message': '钢琴不可用或已被占用'})
        
        # 找到学生的等待记录
        waiting_record = WaitingQueue.objects.filter(
            student=student,
            is_active=True
        ).first()
        
        if not waiting_record:
            return JsonResponse({'success': False, 'message': '找不到该学生的等待记录'})
        
        # 获取相关的考勤会话
        session = waiting_record.session
        
        # 将钢琴设为占用状态
        piano.is_occupied = True
        piano.save()
        
        # 创建考勤记录
        AttendanceRecord.objects.create(
            session=session,
            student=student,
            piano=piano,
            status='checked_in'
        )
        
        # 将等待记录设为非活动
        waiting_record.is_active = False
        waiting_record.save()
        
        return JsonResponse({'success': True, 'message': '钢琴分配成功'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'操作失败: {str(e)}'})


@login_required
@teacher_required
def force_checkout(request):
    """强制学生签退"""
    import logging
    import traceback
    import json
    from django.views.decorators.csrf import csrf_exempt
    from django.utils import timezone
    from mymanage.courses.models import Piano
    from mymanage.students.models import PracticeRecord, Attendance
    from mymanage.attendance.models import AttendanceRecord
    
    logger = logging.getLogger(__name__)
    logger.info(f"收到强制签退请求: method={request.method}, content_type={request.content_type}")
    
    # 检查请求方法
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法不允许'})
    
    # 尝试不同方式获取piano_id
    piano_id = None
    
    # 从请求体获取
    if request.content_type == 'application/x-www-form-urlencoded':
        piano_id = request.POST.get('piano_id')
        logger.info(f"从form表单获取piano_id: {piano_id}")
    # 从查询参数获取
    elif not piano_id:
        piano_id = request.GET.get('piano_id')
        logger.info(f"从URL参数获取piano_id: {piano_id}")
    # 尝试从JSON获取
    if not piano_id and request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            piano_id = data.get('piano_id')
            logger.info(f"从JSON获取piano_id: {piano_id}")
        except json.JSONDecodeError:
            logger.warning("无法解析JSON请求体")
    
    # 尝试从multipart表单获取
    if not piano_id and request.content_type and 'multipart/form-data' in request.content_type:
        piano_id = request.POST.get('piano_id')
        logger.info(f"从multipart表单获取piano_id: {piano_id}")
    
    # 记录所有参数用于调试
    logger.info(f"请求参数: POST={dict(request.POST)}, GET={dict(request.GET)}")
    
    if not piano_id:
        logger.error("缺少必要参数piano_id")
        return JsonResponse({'success': False, 'message': '缺少必要参数piano_id'})
    
    try:
        # 获取钢琴实例
        piano = Piano.objects.get(id=piano_id)
        logger.info(f"找到钢琴: ID={piano_id}, 编号={piano.number}, 状态: 是否可用={piano.is_active}, 是否被占用={piano.is_occupied}")
        
        # 检查是否有前端参数指定的学生信息
        student_name = request.POST.get('student_name') or request.GET.get('student_name')
        logger.info(f"前端提供的学生名称: {student_name}")
        
        # 查找当前使用此钢琴的记录
        current_record = AttendanceRecord.objects.filter(
            piano=piano,
            status='checked_in'
        ).order_by('-check_in_time').first()
        
        if not current_record:
            logger.warning(f"找不到钢琴ID={piano_id}的活跃考勤记录")
            
            # 查找是否有PracticeRecord正在使用此钢琴
            from mymanage.students.models import PracticeRecord
            active_practice = PracticeRecord.objects.filter(
                status='active',
                date=timezone.now().date(),
                piano_number=piano.number
            ).first()
            
            if active_practice:
                logger.info(f"找到活跃的练琴记录: ID={active_practice.id}, 学生={active_practice.student.name}")
                
                # 更新练琴记录状态
                now = timezone.now()
                active_practice.status = 'completed'
                active_practice.end_time = now
                time_diff = (now - active_practice.start_time).total_seconds() // 60
                active_practice.duration = time_diff
                active_practice.save()
                
                # 更新钢琴状态
                piano.is_occupied = False
                piano.save()
                
                logger.info(f"已更新练琴记录状态并释放钢琴")
                return JsonResponse({'success': True, 'message': '已释放钢琴'})
            
            # 确认钢琴状态正确
            if piano.is_occupied:
                logger.warning(f"钢琴显示为占用状态但没有对应的考勤记录，重置钢琴状态")
                piano.is_occupied = False
                piano.save()
                logger.info(f"钢琴状态已重置: ID={piano_id}")
                return JsonResponse({'success': True, 'message': '钢琴状态已重置'})
                
            # 强制性处理 - 即使找不到记录，也标记操作成功
            logger.info(f"找不到相关记录，但仍将操作标记为成功 - 钢琴ID={piano_id}")
            return JsonResponse({'success': True, 'message': '钢琴已标记为可用'})
        
        logger.info(f"找到考勤记录: ID={current_record.id}, 学生={current_record.student.name}")
        
        # 获取学生信息
        student = current_record.student
        today = timezone.now().date()
        
        # 1. 采用学生端签退逻辑处理PracticeRecord
        practice_record = PracticeRecord.objects.filter(
            student=student,
            date=today,
            status='active',
            piano_number=piano.number
        ).first()
        
        if not practice_record:
            # 尝试更宽松的查询
            logger.info(f"未找到精确匹配的练琴记录，尝试宽松查询")
            practice_record = PracticeRecord.objects.filter(
                student=student,
                date=today,
                status='active'
            ).first()
        
        # 如果找到了练琴记录，进行更新
        if practice_record:
            # 计算实际练琴时长
            now = timezone.now()
            actual_duration = (now - practice_record.start_time).total_seconds() // 60
            
            logger.info(f"更新练琴记录: ID={practice_record.id}, 时长={actual_duration}分钟")
            
            try:
                # 更新练琴记录
                practice_record.end_time = now
                practice_record.duration = actual_duration
                practice_record.status = 'completed'
                practice_record.save()
                logger.info(f"练琴记录已更新: ID={practice_record.id}")
            except Exception as e:
                logger.error(f"更新练琴记录失败: {str(e)}\n{traceback.format_exc()}")
            
            # 更新考勤记录
            attendance = Attendance.objects.filter(
                student=student,
                date=today
            ).first()
            
            if attendance:
                try:
                    logger.info(f"更新学生端考勤记录: ID={attendance.id}")
                    attendance.check_out_time = now
                    attendance.save()
                    logger.info(f"学生端考勤记录已更新: ID={attendance.id}")
                except Exception as e:
                    logger.error(f"更新学生端考勤记录失败: {str(e)}\n{traceback.format_exc()}")
        else:
            logger.warning(f"未找到学生{student.name}的练琴记录")
        
        # 2. 调用考勤记录的签退方法
        checkout_success = False
        try:
            logger.info(f"执行AttendanceRecord.check_out方法: record_id={current_record.id}")
            checkout_success = current_record.check_out()
            logger.info(f"AttendanceRecord.check_out结果: {checkout_success}")
        except Exception as e:
            logger.error(f"执行check_out方法失败: {str(e)}\n{traceback.format_exc()}")
            # 如果check_out方法失败，手动更新状态
            try:
                current_record.status = 'checked_out'
                current_record.check_out_time = timezone.now()
                current_record.save()
                logger.info(f"手动更新考勤记录状态成功")
                checkout_success = True
            except Exception as e2:
                logger.error(f"手动更新考勤记录状态也失败: {str(e2)}\n{traceback.format_exc()}")
        
        # 3. 确保钢琴状态已释放（双重保险）
        try:
            piano.is_occupied = False
            piano.save()
            logger.info(f"钢琴状态已重置: id={piano.id}, number={piano.number}")
        except Exception as e:
            logger.error(f"更新钢琴状态失败: {str(e)}\n{traceback.format_exc()}")
        
        # 4. 再次检查钢琴状态（三重保险）
        try:
            piano.refresh_from_db()
            if piano.is_occupied:
                logger.warning(f"钢琴状态更新失败，再次尝试")
                Piano.objects.filter(id=piano_id).update(is_occupied=False)
                logger.info(f"使用update方法更新钢琴状态")
        except Exception as e:
            logger.error(f"第二次尝试更新钢琴状态失败: {str(e)}")
        
        # 记录成功
        logger.info(f"强制签退成功完成: piano_id={piano_id}")
        return JsonResponse({'success': True, 'message': '强制签退成功'})
    
    except Piano.DoesNotExist:
        error_msg = f"找不到ID为{piano_id}的钢琴"
        logger.error(error_msg)
        return JsonResponse({'success': False, 'message': error_msg})
    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"强制签退失败: {str(e)}\n{error_msg}")
        return JsonResponse({'success': False, 'message': f'操作失败: {str(e)}'})


@login_required
@teacher_required
def piano_maintenance(request):
    """将钢琴设置为维护状态"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法不允许'})
    
    piano_id = request.POST.get('piano_id')
    reason = request.POST.get('reason', '维护')
    
    if not piano_id:
        return JsonResponse({'success': False, 'message': '缺少必要参数'})
    
    try:
        from mymanage.courses.models import Piano
        
        piano = Piano.objects.get(id=piano_id)
        
        # 检查钢琴是否已被占用
        if piano.is_occupied:
            return JsonResponse({'success': False, 'message': '钢琴当前正在使用，无法设置为维护状态'})
        
        # 设置钢琴为非活动状态
        piano.is_active = False
        piano.notes = f"维护: {reason} - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        piano.save()
        
        return JsonResponse({'success': True, 'message': '钢琴已设置为维护状态'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'操作失败: {str(e)}'})


@login_required
@teacher_required
def activate_piano(request):
    """恢复钢琴为可用状态"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法不允许'})
    
    piano_id = request.POST.get('piano_id')
    
    if not piano_id:
        return JsonResponse({'success': False, 'message': '缺少必要参数'})
    
    try:
        from mymanage.courses.models import Piano
        
        # 尝试获取钢琴实例，记录原始状态用于调试
        piano = Piano.objects.get(id=piano_id)
        original_active = piano.is_active
        original_occupied = piano.is_occupied
        
        # 打印调试信息
        print(f"恢复钢琴: ID={piano_id}, 编号={piano.number}, 原状态: is_active={original_active}, is_occupied={original_occupied}")
        
        # 恢复钢琴为活动状态
        piano.is_active = True
        piano.is_occupied = False  # 确保钢琴不被占用
        piano.notes = f"{piano.notes}\n恢复使用: {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        piano.save()
        
        # 验证保存结果
        piano.refresh_from_db()
        
        # 检查保存后的状态
        if piano.is_active:
            return JsonResponse({
                'success': True, 
                'message': '钢琴已恢复为可用状态',
                'piano_id': piano_id,
                'piano_number': piano.number,
                'is_active': piano.is_active,
                'is_occupied': piano.is_occupied
            })
        else:
            # 状态未更新成功
            return JsonResponse({
                'success': False,
                'message': '钢琴状态更新失败',
                'piano_id': piano_id,
                'original_active': original_active,
                'original_occupied': original_occupied,
                'current_active': piano.is_active,
                'current_occupied': piano.is_occupied
            })
    
    except Piano.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'找不到ID为 {piano_id} 的钢琴'})
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"恢复钢琴出错: {str(e)}\n{error_traceback}")
        return JsonResponse({'success': False, 'message': f'操作失败: {str(e)}'})


@login_required
@teacher_required
def remove_from_queue(request):
    """从等待队列中移除学生"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法不允许'})
    
    student_id = request.POST.get('student_id')
    
    if not student_id:
        return JsonResponse({'success': False, 'message': '缺少必要参数'})
    
    try:
        from mymanage.students.models import Student
        from mymanage.attendance.models import WaitingQueue
        
        student = Student.objects.get(id=student_id)
        
        # 查找学生的等待记录
        waiting_records = WaitingQueue.objects.filter(
            student=student,
            is_active=True
        )
        
        if not waiting_records.exists():
            return JsonResponse({'success': False, 'message': '找不到该学生的等待记录'})
        
        # 将等待记录设为非活动
        waiting_records.update(is_active=False)
        
        return JsonResponse({'success': True, 'message': '学生已从等待队列中移除'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'操作失败: {str(e)}'})


@login_required
@teacher_required
def student_detail_ajax(request, student_id):
    """通过AJAX获取学生详情"""
    try:
        student = get_object_or_404(Student, id=student_id)
        
        # 准备学生数据
        # 处理性别显示
        gender_display = ""
        gender_value = ""
        if hasattr(student, 'gender'):
            if student.gender == 'male':
                gender_display = "男"
                gender_value = "male"
            elif student.gender == 'female':
                gender_display = "女" 
                gender_value = "female"
        
        student_data = {
            'id': student.id,
            'name': student.name,
            'gender': gender_display,
            'gender_value': gender_value,
            'level': student.level,
            'target_level': student.target_level,
            'phone': student.phone or '未设置',
            'parent_phone': student.parent_phone or '未设置',
            'parent_name': student.parent_name or '未设置',
            'school': student.school or '未设置',
            'avatar_url': student.avatar.url if hasattr(student, 'avatar') and student.avatar else None,
            'created_at': student.created_at.strftime('%Y-%m-%d') if student.created_at else '',
        }
        
        # 添加可能不存在的属性
        if hasattr(student, 'last_practice'):
            student_data['last_practice'] = student.last_practice.strftime('%Y-%m-%d') if student.last_practice else '从未练琴'
        else:
            student_data['last_practice'] = '从未练琴'
            
        if hasattr(student, 'total_practice_time'):
            student_data['total_practice_time'] = student.total_practice_time
        else:
            student_data['total_practice_time'] = 0
            
        if hasattr(student, 'progress'):
            student_data['progress'] = student.progress
        else:
            student_data['progress'] = 0
        
        # 获取最近考勤记录
        attendance_records = AttendanceRecord.objects.filter(
            student=student
        ).order_by('-check_in_time')[:5]
        
        attendance_data = []
        for record in attendance_records:
            session_name = '通用考勤'
            if hasattr(record, 'session') and record.session:
                if hasattr(record.session, 'course') and record.session.course:
                    session_name = record.session.course.name
            
            check_in_time = record.check_in_time.strftime('%Y-%m-%d %H:%M') if record.check_in_time else ''
            check_out_time = record.check_out_time.strftime('%H:%M') if record.check_out_time else '未签退'
            
            duration = '未完成'
            if hasattr(record, 'duration_minutes') and record.duration_minutes is not None:
                # 修正异常持续时间
                duration_value = record.duration_minutes
                if duration_value < 0 or duration_value > 240:
                    # 限制为最大4小时（240分钟）或最小0分钟
                    duration_value = 240 if duration_value > 0 else 0
                duration = f"{int(duration_value)} 分钟"
            
            attendance_data.append({
                'session_name': session_name,
                'check_in_time': check_in_time,
                'check_out_time': check_out_time,
                'duration': duration,
            })
        
        # 返回JSON响应
        return JsonResponse({
            'success': True,
            'student': student_data,
            'attendance_records': attendance_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取学生信息失败: {str(e)}'
        })


@login_required
@teacher_required
def manual_checkin(request):
    """手动添加考勤记录"""
    if request.method == 'POST':
        try:
            teacher = request.user.teacher_profile
            student_id = request.POST.get('student_id')
            course_id = request.POST.get('course_id')
            check_in_time_str = request.POST.get('check_in_time')
            notes = request.POST.get('notes', '')
            session_id = request.POST.get('session_id', '')
            
            # 验证必填字段
            if not student_id or not course_id:
                return JsonResponse({
                    'success': False,
                    'message': '学生和课程为必填项'
                }, status=400)
            
            # 获取学生和课程
            student = get_object_or_404(Student, id=student_id)
            course = get_object_or_404(Course, id=course_id, teacher=teacher)
            
            # 处理考勤时间
            if check_in_time_str:
                check_in_time = timezone.make_aware(datetime.fromisoformat(check_in_time_str))
            else:
                check_in_time = timezone.now()
            
            # 计算签退时间（签到时间+30分钟）
            check_out_time = check_in_time + timezone.timedelta(minutes=30)
            
            # 获取或创建考勤会话
            session = None
            if session_id:
                try:
                    session = AttendanceSession.objects.get(id=session_id, course__teacher=teacher)
                except AttendanceSession.DoesNotExist:
                    pass
            
            if not session:
                # 获取或创建课程时间表
                weekday = check_in_time.weekday()
                schedule, created = CourseSchedule.objects.get_or_create(
                    course=course,
                    weekday=weekday,
                    defaults={
                        'start_time': check_in_time.time(),
                        'end_time': check_out_time.time(),
                        'is_temporary': True
                    }
                )
                
                # 创建考勤会话
                session = AttendanceSession.objects.create(
                    course=course,
                    schedule=schedule,
                    created_by=request.user,
                    start_time=check_in_time,
                    end_time=check_out_time,
                    description=f"手动添加的考勤 - {check_in_time.strftime('%Y-%m-%d %H:%M')}",
                    status='active',
                    is_active=True
                )
            
            # 检查是否已存在相同的考勤记录
            existing_record = AttendanceRecord.objects.filter(
                session=session,
                student=student
            ).first()
            
            if existing_record:
                return JsonResponse({
                    'success': False,
                    'message': f'该学生已有考勤记录，创建于 {existing_record.check_in_time.strftime("%Y-%m-%d %H:%M")}'
                }, status=400)
            
            # 尝试获取1号钢琴，但不实际占用
            from mymanage.courses.models import Piano
            piano = Piano.objects.filter(number=1).first()
            
            # 创建考勤记录（已完成状态）
            record = AttendanceRecord.objects.create(
                session=session,
                student=student,
                check_in_time=check_in_time,
                check_out_time=check_out_time,
                status='checked_out',  # 直接设为已签退
                note=notes,
                duration=0.5,  # 0.5小时
                duration_minutes=30,  # 30分钟
                piano=piano  # 仅关联钢琴，不占用
            )
            
            # 同步创建学生端的考勤记录（已完成状态）
            from mymanage.students.models import Attendance
            
            # 检查是否已存在当天的考勤记录
            existing_attendance = Attendance.objects.filter(
                student=student,
                date=check_in_time.date()
            ).first()
            
            if not existing_attendance:
                # 创建已完成的学生端考勤记录
                Attendance.objects.create(
                    student=student,
                    date=check_in_time.date(),
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,  # 设置签退时间
                    status='present'
                )
            
            # 创建已完成的练琴记录
            from mymanage.students.models import PracticeRecord
            try:
                # 检查是否已存在练琴记录
                existing_practice = PracticeRecord.objects.filter(
                    student=student,
                    date=check_in_time.date(),
                    start_time=check_in_time
                ).exists()
                
                if not existing_practice:
                    # 创建已完成的练琴记录
                    PracticeRecord.objects.create(
                        student=student,
                        date=check_in_time.date(),
                        start_time=check_in_time,
                        end_time=check_out_time,
                        duration=30,  # 30分钟
                        piano_number=1,  # 1号钢琴
                        status='completed',  # 设为已完成
                        attendance_session=session
                    )
                    print(f"为手动添加的考勤记录创建了练琴记录 - 学生: {student.name}")
            except Exception as e:
                print(f"创建练琴记录失败: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'message': '考勤记录添加成功',
                'record': {
                    'id': record.id,
                    'student_name': student.name,
                    'course_name': course.name,
                    'check_in_time': check_in_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'check_out_time': check_out_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': '30分钟'
                }
            })
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            return JsonResponse({
                'success': False,
                'message': f'添加考勤记录时出错: {str(e)}',
                'traceback': error_traceback
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': '仅支持POST请求'
    }, status=405)


@login_required
@teacher_required
def attendance_checkout(request):
    """为学生签退"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法不正确'})
    
    try:
        data = json.loads(request.body)
        record_id = data.get('record_id')
        
        if not record_id:
            return JsonResponse({'success': False, 'message': '参数不完整'})
        
        # 获取考勤记录
        record = get_object_or_404(AttendanceRecord, id=record_id)
        
        # 验证权限
        if record.session.course.teacher.user != request.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': '没有权限执行此操作'})
        
        # 如果记录已经签退，返回错误
        if record.status == 'checked_out':
            return JsonResponse({'success': False, 'message': '该记录已经签退'})
        
        # 更新签退时间和状态
        record.check_out_time = timezone.now()
        record.status = 'checked_out'
        
        # 计算持续时间
        if record.check_in_time:
            duration = record.check_out_time - record.check_in_time
            record.duration = duration.total_seconds() / 3600  # 转换为小时
            record.duration_minutes = duration.total_seconds() / 60  # 转换为分钟
        
        record.save()
        
        # 更新学生的总练琴时长
        student = record.student
        practice_time_hours = getattr(student, 'total_practice_time', 0) or 0
        student.total_practice_time = practice_time_hours + (record.duration or 0)
        student.save()
        
        # 同步更新学生端的考勤记录
        from mymanage.students.models import Attendance
        try:
            # 查找同一天的考勤记录
            attendance = Attendance.objects.filter(
                student=student,
                date=record.check_in_time.date()
            ).first()
            
            if attendance:
                # 更新签退时间
                attendance.check_out_time = record.check_out_time
                attendance.save()
        except Exception as e:
            print(f"更新学生考勤记录失败: {str(e)}")
        
        # 同步添加练习记录
        from mymanage.students.models import PracticeRecord
        try:
            # 添加练习记录
            PracticeRecord.objects.create(
                student=student,
                date=record.check_in_time.date(),
                start_time=record.check_in_time,
                end_time=record.check_out_time,
                duration=int(record.duration_minutes) if record.duration_minutes else 0,
                piano_number=record.piano.number if record.piano else 1
            )
        except Exception as e:
            print(f"添加练习记录失败: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': '签退成功',
            'record': {
                'id': record.id,
                'status': record.status,
                'check_out_time': record.check_out_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': record.duration
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '请求数据格式错误'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'操作失败: {str(e)}'})


@login_required
@teacher_required
def end_session(request):
    """结束考勤会话"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法不正确'})
    
    logger = logging.getLogger(__name__)
    
    try:
        from django.db import models  # 添加导入语句
        
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'success': False, 'message': '参数不完整'})
        
        # 获取考勤会话
        session = get_object_or_404(AttendanceSession, id=session_id)
        
        # 记录调试信息
        logger.debug(f"结束会话: ID={session_id}, 开始时间={session.start_time}, 结束时间={session.end_time}")
        
        # 验证权限
        if session.created_by != request.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': '没有权限执行此操作'})
        
        # 如果会话已经关闭，返回错误
        if session.status != 'active':
            return JsonResponse({'success': False, 'message': '该考勤会话已经关闭'})
        
        # 获取当前时间
        now = timezone.localtime(timezone.now())
        
        # 检查并修复时间异常
        if session.start_time > now:
            logger.warning(f"检测到异常开始时间：{session.start_time} > {now}，进行修正")
            # 将开始时间设置为一小时前
            session.start_time = now - timezone.timedelta(hours=1)
            # 直接保存，跳过验证
            models.Model.save(session)
        
        # 如果有关联的二维码，更新二维码的过期时间为当前时间，使其立即过期
        if session.qrcode:
            logger.debug(f"更新二维码过期时间: ID={session.qrcode.id}, 原过期时间={session.qrcode.expires_at}")
            session.qrcode.expires_at = now
            session.qrcode.save()
            logger.debug(f"二维码已更新: ID={session.qrcode.id}, 新过期时间={now}")
        
        # 关闭会话 - 直接设置相关字段而不使用close_session方法
        session.status = 'closed'
        session.is_active = False
        session.end_time = now
        
        try:
            # 尝试保存会话
            session.save()
        except ValidationError as e:
            logger.error(f"保存会话时验证错误: {e}")
            # 如果保存失败，直接使用原始Model.save方法绕过验证
            models.Model.save(session)
            logger.info("使用绕过验证的方式保存会话成功")
        
        # 为所有未签退的学生自动签退
        active_records = AttendanceRecord.objects.filter(session=session, status='checked_in')
        
        # 导入学生模型
        from mymanage.students.models import Attendance, PracticeRecord
        
        record_count = 0
        for record in active_records:
            try:
                student = record.student
                record.check_out_time = now
                record.status = 'checked_out'
                
                # 计算持续时间
                if record.check_in_time:
                    duration = now - record.check_in_time
                    record.duration = duration.total_seconds() / 3600  # 转换为小时
                    record.duration_minutes = duration.total_seconds() / 60  # 转换为分钟
                
                record.save()
                record_count += 1
                
                # 同步更新学生端考勤记录
                try:
                    # 查找当天的考勤记录
                    attendance = Attendance.objects.filter(
                        student=student,
                        date=record.check_in_time.date()
                    ).first()
                    
                    if attendance:
                        # 更新签退时间
                        attendance.check_out_time = now
                        attendance.save()
                    else:
                        # 如果没有考勤记录，创建一个
                        Attendance.objects.create(
                            student=student,
                            date=record.check_in_time.date(),
                            check_in_time=record.check_in_time,
                            check_out_time=now,
                            status='present'
                        )
                    
                    # 添加练习记录
                    PracticeRecord.objects.create(
                        student=student,
                        date=record.check_in_time.date(),
                        start_time=record.check_in_time,
                        end_time=now,
                        duration=int(record.duration_minutes) if record.duration_minutes else 0,
                        piano_number=record.piano.number if record.piano else 1,
                        status='completed'
                    )
                except Exception as e:
                    logger.error(f"同步学生记录失败: {str(e)}")
            except Exception as e:
                logger.error(f"处理考勤记录时出错: {str(e)}")
        
        return JsonResponse({
            'success': True, 
            'message': '考勤会话已结束',
            'closed_records': record_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '请求数据格式错误'})
    except Exception as e:
        logger.exception(f"结束会话失败: {str(e)}")
        return JsonResponse({'success': False, 'message': f'结束会话失败: {str(e)}'})

@login_required
@teacher_required
def get_students_api(request):
    """获取教师的学生数据API"""
    teacher = request.user.teacher_profile
    students = Student.objects.filter(courses__teacher=teacher).distinct()
    
    # 构建学生数据
    students_data = [{
        'id': student.id,
        'name': student.name,
        'phone': student.phone
    } for student in students]
    
    return JsonResponse({
        'status': 'success',
        'students': students_data
    })

@login_required
@teacher_required
def get_payment_categories_api(request):
    """获取付款类别API"""
    categories = PaymentCategory.objects.all()
    
    categories_data = [{
        'id': category.id,
        'name': category.name
    } for category in categories]
    
    return JsonResponse({
        'status': 'success',
        'categories': categories_data
    })

@login_required
@teacher_required
def add_payment_api(request):
    """添加付款记录API"""
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': '仅支持POST请求'
        }, status=405)
    
    try:
        # 从请求中获取数据
        data = json.loads(request.body)
        student_id = data.get('student_id')
        category_id = data.get('category_id')
        amount = data.get('amount')
        status = data.get('status', 'pending')
        payment_date = data.get('payment_date')
        notes = data.get('notes', '')
        
        # 验证必填字段
        if not all([student_id, category_id, amount]):
            return JsonResponse({
                'status': 'error',
                'message': '缺少必要字段'
            }, status=400)
        
        # 获取相关对象
        teacher = request.user.teacher_profile
        
        try:
            student = Student.objects.get(id=student_id)
            category = PaymentCategory.objects.get(id=category_id)
        except (Student.DoesNotExist, PaymentCategory.DoesNotExist):
            return JsonResponse({
                'status': 'error',
                'message': '学生或付款类别不存在'
            }, status=404)
        
        # 验证学生是否属于当前教师
        if not student.courses.filter(teacher=teacher).exists():
            return JsonResponse({
                'status': 'error',
                'message': '您无权为此学生添加付款记录'
            }, status=403)
        
        # 处理支付日期
        if status == 'paid' and not payment_date:
            payment_date = timezone.now().date()
        elif payment_date:
            try:
                payment_date = timezone.datetime.strptime(payment_date, '%Y-%m-%d').date()
            except ValueError:
                payment_date = None
        
        # 创建支付记录
        payment = Payment.objects.create(
            student=student,
            category=category,
            amount=amount,
            status=status,
            payment_date=payment_date,
            notes=notes
        )
        
        return JsonResponse({
            'status': 'success',
            'message': '付款记录添加成功',
            'payment': {
                'id': payment.id,
                'student_name': student.name,
                'category_name': category.name,
                'amount': float(payment.amount),
                'status': payment.status,
                'payment_date': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else None,
                'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'处理请求时出错: {str(e)}'
        }, status=500)

@login_required
@teacher_required
def mark_payment_as_paid_api(request, payment_id):
    """标记付款状态为已付API"""
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': '仅支持POST请求'
        }, status=405)
    
    teacher = request.user.teacher_profile
    
    try:
        # 获取支付记录
        payment = Payment.objects.get(id=payment_id)
        
        # 验证学生是否属于当前教师
        if not payment.student.courses.filter(teacher=teacher).exists():
            return JsonResponse({
                'status': 'error',
                'message': '您无权修改此付款记录'
            }, status=403)
        
        # 更新支付状态
        payment.status = 'paid'
        
        # 如果没有支付日期，设置为当前日期
        if not payment.payment_date:
            payment.payment_date = timezone.now().date()
        
        payment.save()
        
        return JsonResponse({
            'status': 'success',
            'message': '付款状态已更新',
            'payment': {
                'id': payment.id,
                'status': payment.status,
                'payment_date': payment.payment_date.strftime('%Y-%m-%d')
            }
        })
    
    except Payment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '付款记录不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'处理请求时出错: {str(e)}'
        }, status=500)

@login_required
@teacher_required
def get_payment_stats_api(request):
    """获取付款统计数据API"""
    teacher = request.user.teacher_profile
    
    # 获取当前日期
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # 计算本月和上月的起止日期
    first_day_of_month = today.replace(day=1)
    last_month = (first_day_of_month - timezone.timedelta(days=1)).replace(day=1)
    
    # 获取本月收入
    month_income = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        payment_date__year=current_year,
        payment_date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取上月收入（比较数据）
    last_month_income = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        payment_date__year=last_month.year,
        payment_date__month=last_month.month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 计算同比变化
    month_change_percentage = 0
    if last_month_income > 0:
        month_change_percentage = ((month_income - last_month_income) / last_month_income) * 100
    
    # 获取年度收入
    year_income = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        payment_date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取待收款项
    pending_payments = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='pending'
    )
    total_pending = pending_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # 统计学生人数和已付款学生比例
    total_students = Student.objects.filter(courses__teacher=teacher).distinct().count()
    paid_students = Student.objects.filter(
        courses__teacher=teacher,
        payments__status='paid',
        payments__payment_date__year=current_year,
        payments__payment_date__month=current_month
    ).distinct().count()
    
    paid_percentage = 0
    if total_students > 0:
        paid_percentage = (paid_students / total_students) * 100
    
    # 按类别统计收入数据
    categories = PaymentCategory.objects.all()
    category_data = []
    
    for category in categories:
        category_total = Payment.objects.filter(
            student__courses__teacher=teacher,
            status='paid',
            category=category,
            payment_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if category_total > 0:
            category_data.append({
                'name': category.name,
                'value': float(category_total)
            })
    
    # 按月统计本年度收入
    month_names = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    monthly_income_data = []
    
    for month in range(1, 13):
        # 移除对未来月份的限制，展示全年数据，未发生的月份显示为0
        monthly_total = Payment.objects.filter(
            student__courses__teacher=teacher,
            status='paid',
            payment_date__year=current_year,
            payment_date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_income_data.append({
            'month': month_names[month-1],
            'value': float(monthly_total)
        })
    
    return JsonResponse({
        'status': 'success',
        'stats': {
            'month_income': float(month_income),
            'year_income': float(year_income),
            'month_change_percentage': float(month_change_percentage),
            'total_pending': float(total_pending),
            'total_students': total_students,
            'paid_students': paid_students,
            'paid_percentage': float(paid_percentage),
            'category_data': category_data,
            'monthly_income_data': monthly_income_data,
            'current_month': month_names[current_month-1],
            'current_year': current_year
        }
    }, json_dumps_params={'ensure_ascii': False})

@login_required
@teacher_required
def generate_qrcode_ajax(request):
    # 创建日志记录器
    logger = logging.getLogger(__name__)
    
    # 更新为检查X-Requested-With头来判断AJAX请求
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'GET' and is_ajax:
        try:
            # 获取当前用户（教师）
            teacher = request.user.teacher_profile
            
            # 获取当前的日期和时间，使用系统本地时间
            try:
                now = timezone.localtime(timezone.now())
                logger.info(f"当前系统时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 时间完整性检查
                if now.year < 2024:
                    logger.error(f"系统时间异常: {now} - 年份小于2024")
                    return JsonResponse({
                        'success': False,
                        'message': '系统时间设置异常，年份错误'
                    }, status=500)
                
            except Exception as e:
                logger.error(f"获取系统时间出错: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': '系统时间设置问题，请联系管理员'
                }, status=500)
            
            # 设置过期时间为当天结束
            today_end = now.replace(hour=23, minute=59, second=59)
            expires_at = today_end
            
            # 确保过期时间不早于当前时间
            if expires_at <= now:
                expires_at = now + timezone.timedelta(hours=1)
            
            # 记录时间信息用于调试
            logger.debug(f"生成考勤码 - 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}, 过期时间: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 1. 首先关闭该教师所有现有的活跃会话 - 这一步放在最前面确保清理
            active_sessions = AttendanceSession.objects.filter(
                Q(course__teacher=teacher) | Q(created_by=request.user),
                status='active'
            )
            
            if active_sessions.exists():
                for session in active_sessions:
                    session.status = 'closed'
                    session.is_active = False
                    
                    # 确保会话有结束时间
                    if not session.end_time or session.end_time > now:
                        session.end_time = now
                        
                    session.save()
                    logger.info(f"已关闭会话ID={session.id}, 课程={session.course.name}")
            
            # 检查是否已存在默认课程
            default_course = Course.objects.filter(
                code="DEFAULT",
                teacher=teacher
            ).first()
            
            if not default_course:
                # 获取或创建一个有效的钢琴级别
                piano_level = PianoLevel.objects.first()
                if not piano_level:
                    piano_level = PianoLevel.objects.create(
                        level=1,
                        description="初级"
                    )
                
                # 创建新的默认课程
                default_course = Course.objects.create(
                    name="通用考勤",
                    code="DEFAULT",
                    teacher=teacher,
                    description='自动生成的通用考勤课程',
                    level=piano_level
                )
            
            # 创建二维码
            qrcode_uuid = str(uuid_lib.uuid4())
            qrcode = QRCode.objects.create(
                course=default_course,
                uuid=uuid_lib.UUID(qrcode_uuid),
                code=qrcode_uuid,
                expires_at=expires_at
            )
            
            # 获取当前weekday
            weekday = now.weekday()
            now_time = now.time()
            expires_time = expires_at.time()
            
            # 创建课程时间表，确保使用临时标记
            schedule = None
            try:
                # 尝试获取现有时间表
                schedule = CourseSchedule.objects.get(
                    course=default_course,
                    weekday=weekday,
                    start_time=now_time
                )
                # 更新为临时排课
                schedule.is_temporary = True
                schedule.end_time = expires_time
                schedule.save()
            except CourseSchedule.DoesNotExist:
                # 创建新的临时排课
                schedule = CourseSchedule.objects.create(
                    course=default_course,
                    weekday=weekday,
                    start_time=now_time,
                    end_time=expires_time,
                    is_temporary=True  # 明确标记为临时排课，避免时间验证
                )
            
            # 创建考勤会话
            try:
                # 直接使用从数据库创建记录的方式，避免auto_now_add字段的影响
                session = AttendanceSession(
                    course=default_course,
                    schedule=schedule,
                    qrcode=qrcode,
                    created_by=teacher.user,
                    status='active',
                    is_active=True,
                    description=f"生成于 {now.strftime('%Y-%m-%d %H:%M')}",
                    end_time=expires_at
                )
                # 手动设置开始时间，确保与当前时间一致
                session.start_time = now
                session.save()
                logger.info(f"创建考勤会话成功: ID={session.id}, 开始时间={session.start_time}, 结束时间={session.end_time}")
                
            except ValidationError as ve:
                # 如果创建会话失败，记录并删除已创建的QRCode
                logger.error(f"创建考勤会话时验证错误: {ve}")
                qrcode.delete()
                return JsonResponse({
                    'success': False,
                    'message': f"创建考勤会话失败: {str(ve)}"
                }, status=400)
            
            # 等待二维码图像生成完成
            if not qrcode.qr_code_image:
                qrcode.save()  # 触发save方法生成图像
                qrcode.refresh_from_db()  # 刷新对象以获取生成的图像URL
            
            qr_image_url = qrcode.qr_code_image.url if qrcode.qr_code_image else ''
            
            # 再次检查日期是否正确
            session.refresh_from_db()
            if session.start_time.date() != now.date():
                logger.error(f"检测到日期异常: 会话开始日期={session.start_time.date()}, 当前日期={now.date()}")
                # 直接更新数据库记录
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE attendance_attendancesession SET start_time = %s WHERE id = %s",
                        [now, session.id]
                    )
                session.refresh_from_db()
                logger.info(f"已修正会话时间: 新开始时间={session.start_time}")
            
            # 构建响应数据 - 修改为与前端updateQRCodeDisplay期望的格式一致
            return JsonResponse({
                'success': True,
                'qrcode': {
                    'image_url': qr_image_url,
                    'course_name': default_course.name,
                    'expires_at': expires_at.strftime('%Y-%m-%d %H:%M')
                },
                'session': {
                    'id': session.id,
                    'course_name': default_course.name,
                    'start_time': now.strftime('%Y-%m-%d %H:%M'),
                    'end_time': expires_at.strftime('%Y-%m-%d %H:%M')
                }
            })
        except ValidationError as e:
            # 捕获时间验证错误等情况
            logger.error(f"生成考勤码验证错误: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e),
                'error_details': {
                    'start_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                }
            }, status=400)
        except Exception as e:
            # 记录错误信息到日志
            logger.error(f"生成二维码时出错: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"生成考勤码失败: {str(e)}",
                'error_type': type(e).__name__
            }, status=500)
    
    return JsonResponse({'success': False, 'message': '无效的请求方法'}, status=400)

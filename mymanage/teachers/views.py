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

from mymanage.users.decorators import teacher_required
from .models import TeacherProfile, TeacherCertificate, PrivacySetting
from .forms import TeacherProfileForm, TeacherCertificateForm, TeacherRegistrationForm, PrivacySettingForm, PasswordChangeForm
from mymanage.students.models import Student, PracticeRecord
from mymanage.courses.models import Course, CourseSchedule, SheetMusic, PianoLevel, Piano
from mymanage.attendance.models import AttendanceRecord, AttendanceSession, QRCode, WaitingQueue
from mymanage.finance.models import Payment, PaymentCategory, Fee

@login_required
@teacher_required
def teacher_dashboard(request):
    """教师控制面板视图"""
    teacher = request.user.teacher_profile
    current_time = timezone.now()  # 获取当前时间
    
    # 获取所有学生数量（修改为获取所有学生）
    students_count = Student.objects.count()
    
    # 获取课程数量
    courses_count = Course.objects.filter(teacher=teacher).count()
    
    # 获取今日考勤记录数
    today = timezone.now().date()
    attendance_today = AttendanceRecord.objects.filter(
        check_in_time__date=today
    ).count()
    
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
    
    # 最近的考勤会话
    recent_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher
    ).order_by('-start_time')[:5]
    
    # 获取今日课程 - 使用当前星期几代替日期
    today_weekday = current_time.weekday()  # 获取当前是星期几(0-6，0是周一)
    today_courses = CourseSchedule.objects.filter(
        course__teacher=teacher,
        weekday=today_weekday,
        is_active=True
    ).order_by('start_time')
    
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
    
    # 获取活跃的考勤会话及二维码
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
        'today_courses': today_courses,
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
    
    context = {
        'teacher': teacher,  # 添加教师信息到上下文
        'students': students,
        'total_students': total_students,
        'new_students_this_month': new_students_this_month,
        'level_distribution': level_distribution,
        'recent_students': recent_students,
        'search_query': search_query,
        'unread_notifications_count': 0,  # 为模板提供默认值
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
        messages.success(request, f'学生"{student.name}"信息已更新')
        
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
    
    # 获取今日考勤会话
    today_start = timezone.make_aware(datetime.combine(current_time.date(), datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(current_time.date(), datetime.max.time()))
    
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
    
    # 获取最近的考勤会话
    recent_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher
    ).order_by('-start_time')[:10]
    
    # 检查URL中是否有qrcode参数
    qrcode_uuid = request.GET.get('qrcode')
    qrcode_to_display = None
    
    if qrcode_uuid:
        try:
            qrcode_to_display = QRCode.objects.get(code=qrcode_uuid)
        except QRCode.DoesNotExist:
            pass
    
    # 如果没有指定的二维码，尝试获取最新的活跃二维码
    if not qrcode_to_display and active_sessions.exists():
        active_session = active_sessions.first()
        if hasattr(active_session, 'qrcode') and active_session.qrcode:
            qrcode_to_display = active_session.qrcode
    
    # 如果没有活跃二维码，则自动生成一个
    if not qrcode_to_display:
        try:
            # 先获取或创建一个有效的钢琴级别
            try:
                # 尝试获取第一个现有级别
                piano_level = PianoLevel.objects.first()
                if not piano_level:
                    # 如果没有钢琴级别，先创建一个默认级别
                    piano_level = PianoLevel.objects.create(
                        level=1,
                        description="初级"
                    )
            except Exception as e:
                # 如果获取级别失败，创建一个新级别
                piano_level = PianoLevel.objects.create(
                    level=1,
                    description="初级"
                )
            
            # 检查是否已存在默认课程
            default_course = Course.objects.filter(
                code="DEFAULT",
                teacher=teacher
            ).first()
            
            if default_course:
                course = default_course
            else:
                # 创建新的默认课程
                course = Course.objects.create(
                    name="通用考勤",
                    code="DEFAULT",
                    teacher=teacher,
                    description='自动生成的通用考勤课程',
                    level=piano_level  # 确保提供有效的级别
                )
            
            # 创建二维码，有效期24小时
            expires_at = current_time + timezone.timedelta(hours=24)
            import uuid
            qrcode_uuid = str(uuid.uuid4())
            qrcode_to_display = QRCode.objects.create(
                course=course,
                uuid=uuid.UUID(qrcode_uuid),
                code=qrcode_uuid,
                expires_at=expires_at
            )
            
            # 创建考勤会话
            weekday = current_time.weekday()
            schedule, created = CourseSchedule.objects.get_or_create(
                course=course,
                weekday=weekday,
                defaults={
                    'start_time': current_time.time(),
                    'end_time': expires_at.time(),
                    'is_temporary': True
                }
            )
            
            # 创建考勤会话
            session = AttendanceSession.objects.create(
                course=course,
                schedule=schedule,
                qrcode=qrcode_to_display,
                created_by=request.user,
                start_time=current_time,
                end_time=expires_at,
                description=f"自动生成的考勤 - {current_time.strftime('%Y-%m-%d %H:%M')}",
                status='active'
            )
            
            # 刷新活跃会话列表
            active_sessions = AttendanceSession.objects.filter(
                course__teacher=teacher,
                status='active'
            ).order_by('-start_time')
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            messages.error(request, f"自动生成考勤码时出错: {str(e)}\n{error_traceback}")
    
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
    
    today_attendance_rate = 0
    if today_total_students > 0:
        today_attendance_rate = (today_attended_students / today_total_students) * 100
    
    # 计算周出勤率
    weekly_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        start_time__gte=week_start,
        start_time__lte=week_end
    )
    weekly_total_students = 0
    weekly_attended_students = 0
    
    for session in weekly_sessions:
        enrolled_students = session.course.students.count()
        weekly_total_students += enrolled_students
        attended = AttendanceRecord.objects.filter(session=session).count()
        weekly_attended_students += attended
    
    weekly_attendance_rate = 0
    if weekly_total_students > 0:
        weekly_attendance_rate = (weekly_attended_students / weekly_total_students) * 100
    
    # 计算月出勤率
    monthly_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        start_time__gte=month_start,
        start_time__lte=month_end
    )
    monthly_total_students = 0
    monthly_attended_students = 0
    
    for session in monthly_sessions:
        enrolled_students = session.course.students.count()
        monthly_total_students += enrolled_students
        attended = AttendanceRecord.objects.filter(session=session).count()
        monthly_attended_students += attended
    
    monthly_attendance_rate = 0
    if monthly_total_students > 0:
        monthly_attendance_rate = (monthly_attended_students / monthly_total_students) * 100
    
    # 练琴时长统计
    today_practice_time = PracticeRecord.objects.filter(
        student__courses__teacher=teacher,
        start_time__gte=today_start
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    weekly_practice_time = PracticeRecord.objects.filter(
        student__courses__teacher=teacher,
        start_time__gte=week_start
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    monthly_practice_time = PracticeRecord.objects.filter(
        student__courses__teacher=teacher,
        start_time__gte=month_start
    ).aggregate(total=Sum('duration'))['total'] or 0
    
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
    
    # 今日考勤人数
    attendance_today = AttendanceRecord.objects.filter(
        session__course__teacher=teacher,
        check_in_time__date=current_time.date()
    ).count()
    
    context = {
        'teacher': teacher,
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
        'today_attendance_rate': today_attendance_rate,
        'weekly_attendance_rate': weekly_attendance_rate,
        'monthly_attendance_rate': monthly_attendance_rate,
        'today_practice_time': today_practice_time,
        'weekly_practice_time': weekly_practice_time,
        'monthly_practice_time': monthly_practice_time,
        'today_practice_percentage': today_practice_percentage,
        'weekly_practice_percentage': weekly_practice_percentage,
        'monthly_practice_percentage': monthly_practice_percentage,
        'courses': courses,
        'total_students': total_students,
        'attendance_today': attendance_today,
        'qrcode_to_display': qrcode_to_display
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
            return redirect(f'/teachers/attendance/?qrcode={qrcode_uuid}')
            
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
        return redirect(f'/teachers/attendance/?qrcode={qrcode_uuid}')
    
    return redirect('teachers:attendance')


@login_required
@teacher_required
def attendance_session_detail(request, session_id):
    """考勤会话详情"""
    teacher = request.user.teacher_profile
    session = get_object_or_404(AttendanceSession, id=session_id, course__teacher=teacher)
    
    # 获取考勤记录
    records = AttendanceRecord.objects.filter(session=session).select_related('student')
    
    # 获取未签到的学生
    registered_student_ids = records.values_list('student__id', flat=True)
    absent_students = session.course.students.exclude(id__in=registered_student_ids)
    
    context = {
        'teacher': teacher,
        'session': session,
        'records': records,
        'absent_students': absent_students,
        'total_students': session.course.students.count(),
        'attendance_count': records.count()
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
    records = AttendanceRecord.objects.filter(session__course__teacher=teacher)
    
    # 应用过滤条件
    if course_id:
        records = records.filter(session__course_id=course_id)
    
    if month and year:
        records = records.filter(
            check_in_time__month=month,
            check_in_time__year=year
        )
    
    # 按学生分组统计
    student_stats = records.values('student__name').annotate(
        count=Count('id'),
        total_hours=Sum('duration')
    )
    
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
        level_id = request.POST.get('level')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        
        # 创建曲谱
        sheet = SheetMusic(
            title=title,
            composer=composer,
            level_id=level_id,
            description=description,
            file=file,
            uploaded_by=request.user,
            is_public=request.POST.get('is_public') == 'on'
        )
        
        if 'cover_image' in request.FILES:
            sheet.cover_image = request.FILES['cover_image']
        
        sheet.save()
        messages.success(request, '曲谱添加成功')
        return redirect('teachers:sheet_music')
    
    return render(request, 'teachers/add_sheet_music.html')


@login_required
@teacher_required
def edit_sheet_music(request, sheet_id):
    """编辑曲谱"""
    sheet = get_object_or_404(SheetMusic, id=sheet_id, uploaded_by=request.user)
    
    if request.method == 'POST':
        sheet.title = request.POST.get('title')
        sheet.composer = request.POST.get('composer')
        sheet.level_id = request.POST.get('level')
        sheet.description = request.POST.get('description')
        sheet.is_public = request.POST.get('is_public') == 'on'
        
        if 'file' in request.FILES:
            sheet.file = request.FILES['file']
        
        if 'cover_image' in request.FILES:
            sheet.cover_image = request.FILES['cover_image']
        
        sheet.save()
        messages.success(request, '曲谱更新成功')
        return redirect('teachers:sheet_music_detail', sheet_id=sheet.id)
    
    return render(request, 'teachers/edit_sheet_music.html', {'sheet': sheet})


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
    
    # 获取时间段参数
    period = request.GET.get('period', 'month')
    
    # 获取当前日期
    today = timezone.now().date()
    
    # 获取本月收入
    first_day_of_month = today.replace(day=1)
    month_income = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        created_at__gte=first_day_of_month,
        created_at__lte=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取年度收入
    first_day_of_year = today.replace(month=1, day=1)
    year_income = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        created_at__gte=first_day_of_year,
        created_at__lte=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取待收款项
    pending_payments = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取逾期金额
    overdue_payments = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='overdue'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 获取近期交易记录
    recent_payments = Payment.objects.filter(
        student__courses__teacher=teacher
    ).order_by('-created_at')[:10]
    
    # 准备图表数据
    chart_labels = []
    income_data = []
    
    if period == 'month':
        # 当月收入统计（按天）
        days_in_month = (today.replace(month=today.month % 12 + 1, day=1) - timezone.timedelta(days=1)).day
        for day in range(1, days_in_month + 1):
            date = today.replace(day=day)
            chart_labels.append(f"{day}日")
            
            daily_income = Payment.objects.filter(
                student__courses__teacher=teacher,
                status='paid',
                created_at__date=date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            income_data.append(daily_income)
            
        selected_period = "当月"
    elif period == 'quarter':
        # 本季度收入统计（按周）
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        quarter_start = today.replace(month=quarter_start_month, day=1)
        
        # 按周统计
        current_date = quarter_start
        week_number = 1
        
        while current_date <= today:
            week_end = min(current_date + timezone.timedelta(days=6), today)
            chart_labels.append(f"第{week_number}周")
            
            weekly_income = Payment.objects.filter(
                student__courses__teacher=teacher,
                status='paid',
                created_at__date__gte=current_date,
                created_at__date__lte=week_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            income_data.append(weekly_income)
            
            current_date = week_end + timezone.timedelta(days=1)
            week_number += 1
            
        selected_period = "本季度"
    else:  # year
        # 本年收入统计（按月）
        for month in range(1, 13):
            month_start = today.replace(month=month, day=1)
            if month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timezone.timedelta(days=1)
            else:
                month_end = month_start.replace(month=month + 1, day=1) - timezone.timedelta(days=1)
                
            # 如果是未来月份，则跳过
            if month_start > today:
                continue
                
            chart_labels.append(f"{month}月")
            
            monthly_income = Payment.objects.filter(
                student__courses__teacher=teacher,
                status='paid',
                created_at__date__gte=month_start,
                created_at__date__lte=min(month_end, today)
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            income_data.append(monthly_income)
            
        selected_period = "本年"
    
    # 收入分类饼图数据
    categories = PaymentCategory.objects.all()
    category_labels = []
    category_data = []
    
    for category in categories:
        category_total = Payment.objects.filter(
            student__courses__teacher=teacher,
            status='paid',
            category=category,
            created_at__gte=first_day_of_year,
            created_at__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if category_total > 0:
            category_labels.append(category.name)
            category_data.append(category_total)
    
    context = {
        'teacher': teacher,
        'month_income': month_income,
        'year_income': year_income,
        'pending_payments': pending_payments,
        'overdue_payments': overdue_payments,
        'recent_payments': recent_payments,
        'chart_labels': json.dumps(chart_labels),
        'income_data': json.dumps(income_data),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'selected_period': selected_period,
        'unread_notifications_count': 0,  # 为模板提供默认值
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
    current_time = timezone.now()
    
    # 添加调试日志
    print(f"当前时间: {current_time}")
    print(f"当前教师: {teacher.name}")
    
    # 获取所有钢琴及其状态
    pianos = Piano.objects.all().order_by('number')
    print(f"系统中钢琴数量: {pianos.count()}")
    
    # 为每个钢琴添加当前使用学生信息
    for piano in pianos:
        if piano.is_active and piano.is_occupied:
            # 查找当前使用此钢琴的学生
            current_record = AttendanceRecord.objects.filter(
                piano=piano,
                status='checked_in',
                check_in_time__lte=current_time
            ).order_by('-check_in_time').first()
            
            if current_record:
                piano.current_student = current_record.student
                piano.start_time = current_record.check_in_time
                piano.end_time = current_record.check_in_time + timedelta(minutes=30)  # 标准练习时长30分钟
                
                # 计算已练习时间
                practiced_minutes = int((current_time - current_record.check_in_time).total_seconds() / 60)
                piano.practiced_time = f"{practiced_minutes}分钟"
                print(f"钢琴{piano.number}被{current_record.student.name}使用中，已练习{practiced_minutes}分钟")
            else:
                # 这里是错误状态：钢琴标记为占用，但没有对应的考勤记录
                print(f"警告: 钢琴{piano.number}标记为占用，但找不到对应的考勤记录")
                # 修正钢琴状态
                piano.is_occupied = False
                piano.save()
        else:
            print(f"钢琴{piano.number} - 状态: {'可用' if piano.is_active else '维护中'}，{'被占用' if piano.is_occupied else '空闲'}")
    
    # 获取当前等待队列中的学生
    waiting_students = []
    active_waiters = WaitingQueue.objects.filter(
        is_active=True,
        session__status='active'
    ).order_by('join_time')
    
    print(f"等待队列学生数量: {active_waiters.count()}")
    for waiter in active_waiters:
        waiting_time = int((current_time - waiter.join_time).total_seconds() / 60)
        estimated_start = waiter.join_time + timedelta(minutes=waiter.estimated_wait_time)
        
        waiting_students.append({
            'id': waiter.student.id,
            'name': waiter.student.name,
            'level': waiter.student.get_level_display() if hasattr(waiter.student, 'get_level_display') else f"{waiter.student.level}级",
            'wait_time': waiting_time,
            'estimated_start_time': estimated_start,
        })
        print(f"等待学生: {waiter.student.name}，等待时间: {waiting_time}分钟")
    
    # 获取可用钢琴列表（用于手动分配）
    available_pianos = Piano.objects.filter(is_active=True, is_occupied=False)
    
    # 获取今日签到记录
    today_records = AttendanceRecord.objects.filter(
        check_in_time__date=current_time.date()
    ).order_by('-check_in_time')
    
    print(f"今日签到记录数: {today_records.count()}")
    for record in today_records:
        print(f"签到记录: {record.student.name} - 状态: {record.status} - 钢琴: {record.piano.number if record.piano else '无'}")
    
    # 计算统计信息
    checked_in_today = AttendanceRecord.objects.filter(
        check_in_time__date=current_time.date()
    ).count()
    
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
        print(f"自动签退超时记录: {record.student.name} - 签到时间: {record.check_in_time}")
        record.check_out()
    
    context = {
        'teacher': teacher,
        'pianos': pianos,
        'waiting_students': waiting_students,
        'available_pianos': available_pianos,
        'today_records': today_records,
        'current_time': current_time,
        'checked_in_today': checked_in_today,
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
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法不允许'})
    
    piano_id = request.POST.get('piano_id')
    
    if not piano_id:
        return JsonResponse({'success': False, 'message': '缺少必要参数'})
    
    try:
        from mymanage.courses.models import Piano
        
        piano = Piano.objects.get(id=piano_id)
        
        # 查找当前使用此钢琴的记录
        current_record = AttendanceRecord.objects.filter(
            piano=piano,
            status='checked_in'
        ).order_by('-check_in_time').first()
        
        if not current_record:
            return JsonResponse({'success': False, 'message': '找不到相关考勤记录'})
        
        # 执行签退操作
        current_record.check_out()
        
        return JsonResponse({'success': True, 'message': '强制签退成功'})
    
    except Exception as e:
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
            session_name = '未知课程'
            if hasattr(record, 'session') and record.session:
                if hasattr(record.session, 'course') and record.session.course:
                    session_name = record.session.course.name
            
            check_in_time = record.check_in_time.strftime('%Y-%m-%d %H:%M') if record.check_in_time else ''
            check_out_time = record.check_out_time.strftime('%H:%M') if record.check_out_time else '未签退'
            
            duration = '未完成'
            if hasattr(record, 'duration_minutes') and record.duration_minutes:
                duration = f"{record.duration_minutes} 分钟"
            
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

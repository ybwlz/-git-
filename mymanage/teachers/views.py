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

from mymanage.users.decorators import teacher_required
from .models import TeacherProfile, TeacherCertificate, PrivacySetting
from .forms import TeacherProfileForm, TeacherCertificateForm, TeacherRegistrationForm, PrivacySettingForm, PasswordChangeForm
from mymanage.students.models import Student, PracticeRecord
from mymanage.courses.models import Course, CourseSchedule, SheetMusic, PianoLevel
from mymanage.attendance.models import AttendanceRecord, AttendanceSession, QRCode
from mymanage.finance.models import Payment, PaymentCategory, Fee

@login_required
@teacher_required
def teacher_dashboard(request):
    """教师仪表板"""
    teacher = request.user.teacher_profile
    
    # 获取当前时间以确保一致性
    current_time = timezone.now()
    today = current_time.date()
    
    # 获取基本统计数据
    students_count = Student.objects.filter(
        courses__teacher=teacher, 
        courses__is_active=True
    ).distinct().count()
    
    courses_count = Course.objects.filter(teacher=teacher).count()
    
    # 获取今日考勤记录
    attendance_today = AttendanceRecord.objects.filter(
        session__course__teacher=teacher,
        check_in_time__date=today
    ).count()
    
    # 获取本月收款金额
    month_start = today.replace(day=1)
    payments_this_month = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        payment_date__gte=month_start,
        payment_date__lte=today
    ).aggregate(total=Sum('amount'))
    
    # 获取本年收入
    year_start = today.replace(month=1, day=1)
    yearly_income = Payment.objects.filter(
        student__courses__teacher=teacher,
        status='paid',
        payment_date__gte=year_start,
        payment_date__lte=today
    ).aggregate(total=Sum('amount'))
    
    # 获取待缴学费
    pending_payments = Payment.objects.filter(
        student__courses__teacher=teacher,
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
        count = Student.objects.filter(
            courses__teacher=teacher,
            courses__is_active=True,
            level=i
        ).distinct().count()
        student_levels.append({
            'name': level_name,
            'count': count
        })
    
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
        
        if action == 'update_profile':
            form = TeacherProfileForm(request.POST, request.FILES, instance=teacher_profile)
            if form.is_valid():
                form.save()
                messages.success(request, '个人信息更新成功！')
                return redirect('teachers:profile')
        
        elif action == 'update_privacy':
            form = PrivacySettingForm(request.POST, instance=privacy_settings)
            if form.is_valid():
                form.save()
                messages.success(request, '隐私设置更新成功！')
                return redirect('teachers:profile')
        
        elif action == 'change_password':
            form = PasswordChangeForm(request.POST)
            if form.is_valid():
                if request.user.check_password(form.cleaned_data['old_password']):
                    request.user.set_password(form.cleaned_data['new_password'])
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, '密码修改成功！')
                else:
                    messages.error(request, '当前密码不正确！')
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
    
    # 获取该教师相关的所有学生
    students = Student.objects.filter(
        courses__teacher=teacher, 
        courses__is_active=True
    ).distinct()
    
    # 应用搜索过滤
    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) | 
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # 统计数据
    total_students = students.count()
    
    # 本月新增学生数
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_students_this_month = Student.objects.filter(
        courses__teacher=teacher,
        courses__is_active=True,
        created_at__gte=first_day_of_month
    ).distinct().count()
    
    # 计算平均出勤率
    last_30_days = today - timezone.timedelta(days=30)
    total_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        start_time__gte=last_30_days
    ).count()
    
    if total_sessions > 0:
        attended_records = AttendanceRecord.objects.filter(
            session__course__teacher=teacher,
            session__start_time__gte=last_30_days
        ).count()
        attendance_rate = (attended_records / total_sessions) * 100
    else:
        attendance_rate = 0
    
    # 今日练琴人数
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_attendance = PracticeRecord.objects.filter(
        student__courses__teacher=teacher,
        start_time__gte=today_start
    ).values('student').distinct().count()
    
    # 分页处理
    paginator = Paginator(students, 10)  # 每页10个学生
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取钢琴级别选项（用于添加学生表单）
    piano_levels = PianoLevel.objects.all()
    
    context = {
        'teacher': teacher,
        'students': page_obj,  # 分页后的学生
        'total_students': total_students,
        'new_students_this_month': new_students_this_month,
        'attendance_rate': attendance_rate,
        'today_attendance': today_attendance,
        'piano_levels': piano_levels,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'page_obj': page_obj,
        'unread_notifications_count': 0,  # 为模板提供默认值
    }
    
    return render(request, 'teachers/teacher_students.html', context)


@login_required
@teacher_required
def student_detail(request, student_id):
    """学生详情"""
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, id=student_id)
    
    # 确认该学生是否与教师相关
    courses = Course.objects.filter(teacher=teacher, students=student, is_active=True)
    if not courses.exists():
        messages.error(request, '您无权查看此学生信息')
        return redirect('teacher_students')
    
    # 获取学生考勤记录
    attendance_records = AttendanceRecord.objects.filter(
        student=student,
        session__course__teacher=teacher
    ).order_by('-check_in_time')[:10]
    
    context = {
        'student': student,
        'courses': courses,
        'attendance_records': attendance_records
    }
    
    return render(request, 'teachers/student_detail.html', context)


@login_required
@teacher_required
def add_student(request):
    """添加学生"""
    if request.method == 'POST':
        # 处理表单提交
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        parent_phone = request.POST.get('parent_phone')
        level_id = request.POST.get('level')
        birthday = request.POST.get('birthday')
        notes = request.POST.get('notes')
        avatar = request.FILES.get('avatar')
        
        # 创建学生记录
        student = Student(
            name=name,
            gender=gender,
            phone=phone,
            parent_phone=parent_phone,
            birthday=birthday,
            notes=notes
        )
        
        if avatar:
            student.avatar = avatar
            
        if level_id:
            piano_level = get_object_or_404(PianoLevel, id=level_id)
            student.level = piano_level.level
            
        student.save()
        
        # 将学生添加到教师的某门课程
        messages.success(request, f'学生"{name}"已成功添加')
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
        student.gender = request.POST.get('gender', student.gender)
        student.phone = request.POST.get('phone', student.phone)
        student.parent_phone = request.POST.get('parent_phone', student.parent_phone)
        
        level_id = request.POST.get('level')
        if level_id:
            piano_level = get_object_or_404(PianoLevel, id=level_id)
            student.level = piano_level.level
            
        birthday = request.POST.get('birthday')
        if birthday:
            student.birthday = birthday
            
        student.notes = request.POST.get('notes', student.notes)
        
        avatar = request.FILES.get('avatar')
        if avatar:
            student.avatar = avatar
            
        student.save()
        messages.success(request, f'学生"{student.name}"信息已更新')
        return redirect('teachers:students')
    
    # GET请求，显示编辑表单
    piano_levels = PianoLevel.objects.all()
    return render(request, 'teachers/edit_student.html', {
        'student': student,
        'piano_levels': piano_levels
    })


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
    """教师的课程列表"""
    teacher = request.user.teacher_profile
    courses = Course.objects.filter(teacher=teacher)
    
    return render(request, 'teachers/teacher_courses.html', {'courses': courses})


@login_required
@teacher_required
def course_detail(request, course_id):
    """课程详情"""
    teacher = request.user.teacher_profile
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    # 获取课程学生
    students = course.students.all()
    
    # 获取课程安排
    schedules = CourseSchedule.objects.filter(course=course).order_by('date', 'start_time')
    
    context = {
        'teacher': teacher,
        'course': course,
        'students': students,
        'schedules': schedules,
    }
    
    return render(request, 'teachers/course_detail.html', context)


@login_required
@teacher_required
def add_course(request):
    """添加课程"""
    return render(request, 'teachers/add_course.html')


@login_required
@teacher_required
def edit_course(request, course_id):
    """编辑课程"""
    teacher = request.user.teacher_profile
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    return render(request, 'teachers/edit_course.html', {'course': course})


@login_required
@teacher_required
def teacher_attendance(request):
    """教师考勤记录"""
    teacher = request.user.teacher_profile
    
    # 处理二维码显示参数
    qrcode_param = request.GET.get('qrcode')
    if qrcode_param:
        # 查找二维码
        try:
            from mymanage.attendance.models import QRCode
            qrcode = QRCode.objects.filter(
                Q(uuid=qrcode_param) | Q(code=qrcode_param),
                course__teacher=teacher
            ).first()
            
            if qrcode:
                # 设置上下文中的二维码，用于前端显示
                qrcode_to_display = qrcode
            else:
                messages.warning(request, '找不到指定的二维码')
                qrcode_to_display = None
        except Exception as e:
            messages.error(request, f'处理二维码参数出错: {str(e)}')
            qrcode_to_display = None
    else:
        qrcode_to_display = None
    
    # 获取活跃考勤
    active_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        status__in=['active', 'pending']
    ).order_by('start_time')
    
    # 为每个考勤添加更多数据
    for session in active_sessions:
        # 计算已到学生人数
        session.attendance_count = AttendanceRecord.objects.filter(session=session).count()
        # 总学生人数
        session.total_students = session.course.students.count()
    
    # 获取近期考勤记录
    recent_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher
    ).order_by('-start_time')[:10]
    
    # 为每个考勤添加更多数据
    for session in recent_sessions:
        # 计算已到学生人数
        session.attendance_count = AttendanceRecord.objects.filter(session=session).count()
        # 总学生人数
        session.total_students = session.course.students.count()
    
    # 统计今日考勤
    today = timezone.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    attendance_today = AttendanceRecord.objects.filter(
        session__course__teacher=teacher,
        check_in_time__gte=today_start
    ).values('student').distinct().count()
    
    # 统计本周出勤率
    week_start = today - timezone.timedelta(days=today.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        start_time__gte=week_start
    )
    week_total_students = 0
    week_attended_students = 0
    
    for session in week_sessions:
        enrolled_students = session.course.students.count()
        week_total_students += enrolled_students
        attended = AttendanceRecord.objects.filter(session=session).count()
        week_attended_students += attended
    
    weekly_attendance_rate = 0
    if week_total_students > 0:
        weekly_attendance_rate = (week_attended_students / week_total_students) * 100
    
    # 统计本月出勤率
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_sessions = AttendanceSession.objects.filter(
        course__teacher=teacher,
        start_time__gte=month_start
    )
    month_total_students = 0
    month_attended_students = 0
    
    for session in month_sessions:
        enrolled_students = session.course.students.count()
        month_total_students += enrolled_students
        attended = AttendanceRecord.objects.filter(session=session).count()
        month_attended_students += attended
    
    monthly_attendance_rate = 0
    if month_total_students > 0:
        monthly_attendance_rate = (month_attended_students / month_total_students) * 100
    
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
    
    # 计算总学生数
    total_students = Student.objects.filter(
        courses__teacher=teacher,
        courses__is_active=True
    ).distinct().count()
    
    context = {
        'teacher': teacher,
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
        'attendance_today': attendance_today,
        'weekly_attendance_rate': weekly_attendance_rate,
        'monthly_attendance_rate': monthly_attendance_rate,
        'today_attendance_rate': today_attendance_rate,
        'today_practice_time': today_practice_time,
        'weekly_practice_time': weekly_practice_time,
        'monthly_practice_time': monthly_practice_time,
        'today_practice_percentage': today_practice_percentage,
        'weekly_practice_percentage': weekly_practice_percentage,
        'monthly_practice_percentage': monthly_practice_percentage,
        'courses': courses,
        'total_students': total_students,
        'unread_notifications_count': 0,  # 为模板提供默认值
        'qrcode_to_display': qrcode_to_display,  # 添加要显示的二维码
    }
    
    return render(request, 'teachers/teacher_attendance.html', context)


@login_required
@teacher_required
def generate_qrcode(request):
    """生成考勤二维码"""
    if request.method == 'POST':
        teacher = request.user.teacher_profile
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
        
        # 检查是否已有活跃的考勤会话
        active_session = AttendanceSession.objects.filter(
            course=course,
            status='active'
        ).first()
        
        if active_session:
            # 关闭已有的活跃会话
            active_session.status = 'closed'
            active_session.end_time = timezone.now()
            active_session.save()
        
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
    sheet_music_list = SheetMusic.objects.filter(uploaded_by=request.user)
    
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
        return redirect('teacher_sheet_music')
    
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
        return redirect('teacher_sheet_music_detail', sheet_id=sheet.id)
    
    return render(request, 'teachers/edit_sheet_music.html', {'sheet': sheet})


@login_required
@teacher_required
def delete_sheet_music(request, sheet_id):
    """删除曲谱"""
    sheet = get_object_or_404(SheetMusic, id=sheet_id, uploaded_by=request.user)
    
    if request.method == 'POST':
        sheet.delete()
        messages.success(request, '曲谱已删除')
        return redirect('teacher_sheet_music')
    
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
def show_qrcode(request, qrcode_id):
    """显示指定的二维码"""
    qrcode = get_object_or_404(QRCode, uuid=qrcode_id)
    
    # 检查权限
    if qrcode.course.teacher != request.user.teacher_profile:
        messages.error(request, '您没有权限查看此二维码')
        return redirect('teachers:attendance')
    
    context = {
        'qrcode': qrcode,
        'session': qrcode.session
    }
    
    return render(request, 'teachers/show_qrcode.html', context)

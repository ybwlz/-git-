from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json

from .models import QRCode, AttendanceSession, AttendanceRecord, WaitingQueue
from .forms import QRCodeForm, AttendanceSessionForm, StudentCheckInForm, StudentCheckOutForm
from mymanage.courses.models import Course, Piano
from mymanage.students.models import Student


@login_required
def record_attendance(request):
    """
    考勤记录页面，根据用户类型显示不同的页面
    """
    user = request.user
    
    # 教师用户
    if hasattr(user, 'teacher_profile'):
        # 获取当前教师的所有课程
        courses = Course.objects.filter(teacher=user.teacher_profile)
        
        if request.method == 'POST':
            form = AttendanceSessionForm(request.POST, user=user)
            if form.is_valid():
                session = form.save(user=user)
                messages.success(request, f'已创建考勤会话: {session.course.name}')
                return redirect('attendance:session_detail', pk=session.id)
        else:
            form = AttendanceSessionForm(user=user)
        
        # 获取该教师的所有考勤会话，按时间倒序
        sessions = AttendanceSession.objects.filter(
            course__teacher=user.teacher_profile
        ).order_by('-start_time')
        
        # 今日考勤会话
        today = timezone.now().date()
        today_sessions = sessions.filter(start_time__date=today)
        
        return render(request, 'attendance/teacher_attendance.html', {
            'form': form,
            'sessions': sessions,
            'today_sessions': today_sessions,
            'courses': courses,
        })
    
    # 学生用户
    elif hasattr(user, 'student_profile'):
        student = user.student_profile
        
        # 获取学生所有考勤记录
        records = AttendanceRecord.objects.filter(
            student=student
        ).order_by('-check_in_time')
        
        # 获取学生当前活跃的考勤记录
        active_record = records.filter(status='checked_in').first()
        
        # 获取学生是否在等待队列中
        in_queue = WaitingQueue.objects.filter(
            student=student,
            is_active=True
        ).exists()
        
        # 学生打卡统计
        today = timezone.now().date()
        today_record = records.filter(check_in_time__date=today).first()
        
        last_week = today - timedelta(days=7)
        week_records = records.filter(check_in_time__date__gte=last_week)
        
        # 统计学习时间
        total_duration = timedelta()
        for record in records.exclude(duration=None):
            total_duration += record.duration or timedelta()
        
        weekly_duration = timedelta()
        for record in week_records.exclude(duration=None):
            weekly_duration += record.duration or timedelta()
        
        return render(request, 'attendance/student_attendance.html', {
            'student': student,
            'records': records[:10],  # 最近10条记录
            'active_record': active_record,
            'in_queue': in_queue,
            'today_record': today_record,
            'total_duration': total_duration,
            'weekly_duration': weekly_duration,
        })
    
    # 管理员用户
    else:
        # 获取所有考勤会话
        sessions = AttendanceSession.objects.all().order_by('-start_time')
        
        # 今日会话
        today = timezone.now().date()
        today_sessions = sessions.filter(start_time__date=today)
        
        # 活跃会话
        active_sessions = sessions.filter(status='active')
        
        # 考勤统计
        today_records = AttendanceRecord.objects.filter(check_in_time__date=today)
        
        return render(request, 'attendance/admin_attendance.html', {
            'sessions': sessions[:20],  # 最近20条会话
            'today_sessions': today_sessions,
            'active_sessions': active_sessions,
            'today_records_count': today_records.count(),
        })


@login_required
def session_detail(request, pk):
    """
    考勤会话详情页面
    """
    session = get_object_or_404(AttendanceSession, pk=pk)
    
    # 获取会话的所有考勤记录
    records = AttendanceRecord.objects.filter(session=session)
    
    # 获取等待队列
    waiting_queue = WaitingQueue.objects.filter(
        session=session,
        is_active=True
    ).order_by('join_time')
    
    # 获取可用钢琴
    available_pianos = Piano.objects.filter(is_occupied=False)
    
    context = {
        'session': session,
        'records': records,
        'waiting_queue': waiting_queue,
        'available_pianos': available_pianos,
    }
    
    # 如果是教师，可以关闭会话
    if request.user.is_staff or (hasattr(request.user, 'teacher_profile') and 
                                session.course.teacher == request.user.teacher_profile):
        if request.method == 'POST' and 'close_session' in request.POST:
            session.close_session()
            messages.success(request, f'会话 {session.course.name} 已关闭')
            return redirect('attendance:record')
    
    return render(request, 'attendance/session_detail.html', context)


@login_required
def generate_qrcode(request, course_id):
    """
    生成二维码页面
    """
    course = get_object_or_404(Course, pk=course_id)
    
    # 检查权限：只有教师本人或管理员可以生成二维码
    if not request.user.is_staff and (not hasattr(request.user, 'teacher_profile') or 
                                       course.teacher != request.user.teacher_profile):
        messages.error(request, '您没有权限执行此操作')
        return redirect('attendance:record')
    
    if request.method == 'POST':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qrcode = form.save(commit=False)
            qrcode.course = course
            qrcode.save()
            
            messages.success(request, f'已生成 {course.name} 的二维码')
            
            # 查找或创建考勤会话
            today = timezone.now().date()
            session = AttendanceSession.objects.filter(
                course=course,
                start_time__date=today,
                status='active'
            ).first()
            
            if not session:
                # 查找今天的课程安排
                schedule = course.schedules.filter(
                    weekday=today.weekday()
                ).first()
                
                if schedule:
                    session = AttendanceSession.objects.create(
                        course=course,
                        schedule=schedule,
                        created_by=request.user,
                        qrcode=qrcode
                    )
            else:
                session.qrcode = qrcode
                session.save()
                
            if session:
                return redirect('attendance:session_detail', pk=session.id)
            return redirect('attendance:qrcode_detail', pk=qrcode.id)
    else:
        form = QRCodeForm(initial={'course': course})
    
    return render(request, 'attendance/generate_qrcode.html', {
        'form': form,
        'course': course,
    })


@login_required
def qrcode_detail(request, pk):
    """
    二维码详情页面
    """
    qrcode = get_object_or_404(QRCode, pk=pk)
    
    # 检查权限：只有教师本人或管理员可以查看二维码
    if not request.user.is_staff and (not hasattr(request.user, 'teacher_profile') or 
                                       qrcode.course.teacher != request.user.teacher_profile):
        messages.error(request, '您没有权限执行此操作')
        return redirect('attendance:record')
    
    return render(request, 'attendance/qrcode_detail.html', {
        'qrcode': qrcode,
    })


@login_required
def student_check_in(request):
    """
    学生签到API
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '方法不允许'})
    
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'status': 'error', 'message': '只有学生用户可以签到'})
    
    student = request.user.student_profile
    
    # 检查学生是否已经签到但未签退
    active_record = AttendanceRecord.objects.filter(
        student=student,
        status='checked_in'
    ).first()
    
    if active_record:
        return JsonResponse({
            'status': 'error', 
            'message': '您已经签到，请先签退',
            'record_id': active_record.id
        })
    
    # 检查学生是否已在等待队列中
    in_queue = WaitingQueue.objects.filter(
        student=student,
        is_active=True
    ).exists()
    
    if in_queue:
        return JsonResponse({'status': 'error', 'message': '您已在等待队列中'})
    
    form = StudentCheckInForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'status': 'error', 'message': form.errors.as_text()})
    
    uuid = form.cleaned_data['qrcode_uuid']
    qrcode = QRCode.objects.get(uuid=uuid)
    session = qrcode.session
    
    # 检查学生是否已经报名该课程
    enrolled = student.enrollments.filter(course=session.course, status='active').exists()
    if not enrolled:
        return JsonResponse({'status': 'error', 'message': '您未报名该课程'})
    
    # 查找可用钢琴
    available_piano = Piano.objects.filter(is_occupied=False).first()
    
    if available_piano:
        # 有可用钢琴，直接分配并创建考勤记录
        available_piano.is_occupied = True
        available_piano.save()
        
        record = AttendanceRecord.objects.create(
            session=session,
            student=student,
            piano=available_piano
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'签到成功！已分配钢琴{available_piano.piano_number}号',
            'record_id': record.id,
            'piano': available_piano.piano_number
        })
    else:
        # 没有可用钢琴，加入等待队列
        # 计算预计等待时间：每人15分钟
        queue_count = WaitingQueue.objects.filter(
            session=session,
            is_active=True
        ).count()
        
        estimated_time = queue_count * 15  # 每人预计15分钟
        
        # 创建等待记录
        waiting = WaitingQueue.objects.create(
            session=session,
            student=student,
            estimated_wait_time=estimated_time
        )
        
        return JsonResponse({
            'status': 'waiting',
            'message': '当前没有可用钢琴，已加入等待队列',
            'position': queue_count + 1,
            'estimated_time': estimated_time
        })


@login_required
def student_check_out(request):
    """
    学生签退API
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '方法不允许'})
    
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'status': 'error', 'message': '只有学生用户可以签退'})
    
    student = request.user.student_profile
    
    form = StudentCheckOutForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'status': 'error', 'message': form.errors.as_text()})
    
    record_id = form.cleaned_data['record_id']
    record = AttendanceRecord.objects.get(id=record_id)
    
    # 检查权限：只有学生本人可以签退
    if record.student != student:
        return JsonResponse({'status': 'error', 'message': '您没有权限执行此操作'})
    
    # 执行签退
    success = record.check_out()
    
    if success:
        duration = record.duration
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        
        return JsonResponse({
            'status': 'success',
            'message': f'签退成功！学习时长: {int(hours)}小时{int(minutes)}分钟',
            'duration': str(duration)
        })
    else:
        return JsonResponse({'status': 'error', 'message': '签退失败，该记录可能已签退'})


@login_required
def attendance_statistics(request):
    """
    考勤统计页面
    """
    user = request.user
    
    if hasattr(user, 'teacher_profile'):
        teacher = user.teacher_profile
        courses = Course.objects.filter(teacher=teacher)
        
        # 获取所有学生的考勤记录
        course_stats = []
        for course in courses:
            records = AttendanceRecord.objects.filter(session__course=course)
            total_duration = timedelta()
            for record in records.exclude(duration=None):
                total_duration += record.duration or timedelta()
            
            students_count = course.enrollments.filter(status='active').count()
            
            course_stats.append({
                'course': course,
                'total_records': records.count(),
                'total_duration': total_duration,
                'students_count': students_count
            })
            
        return render(request, 'attendance/teacher_statistics.html', {
            'teacher': teacher,
            'course_stats': course_stats
        })
    
    elif hasattr(user, 'student_profile'):
        student = user.student_profile
        
        # 获取学生的所有考勤记录
        records = AttendanceRecord.objects.filter(student=student)
        
        # 计算总学习时间
        total_duration = timedelta()
        for record in records.exclude(duration=None):
            total_duration += record.duration or timedelta()
        
        # 按月统计学习时间
        monthly_stats = {}
        for record in records.exclude(duration=None):
            month_key = record.check_in_time.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'month': record.check_in_time.strftime('%Y年%m月'),
                    'duration': timedelta()
                }
            monthly_stats[month_key]['duration'] += record.duration or timedelta()
        
        # 转换为列表并排序
        monthly_stats = [v for k, v in sorted(monthly_stats.items(), reverse=True)]
        
        return render(request, 'attendance/student_statistics.html', {
            'student': student,
            'total_records': records.count(),
            'total_duration': total_duration,
            'monthly_stats': monthly_stats
        })
    
    # 管理员用户
    else:
        # 所有课程统计
        courses = Course.objects.all()
        
        # 所有学生统计
        students = Student.objects.all()
        
        # 考勤统计
        all_records = AttendanceRecord.objects.all()
        total_duration = timedelta()
        for record in all_records.exclude(duration=None):
            total_duration += record.duration or timedelta()
        
        return render(request, 'attendance/admin_statistics.html', {
            'courses_count': courses.count(),
            'students_count': students.count(),
            'records_count': all_records.count(),
            'total_duration': total_duration
        })

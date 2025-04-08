from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from datetime import datetime, timedelta
import json
import qrcode
from io import BytesIO
import base64
from django.db.models import Sum, Count, Avg, Q, Max, Avg
from django.db.models import Count, Sum, F, Avg, ExpressionWrapper, DurationField
from django.db.models.functions import TruncMonth, Extract
from django.db import connection
import calendar
import traceback
import logging

from .models import Student, PracticeRecord, Attendance, StudentFavorite
from .forms import StudentProfileForm, PracticeRecordForm, AttendanceForm, SheetMusicSearchForm

logger = logging.getLogger(__name__)

@login_required
def profile(request):
    student = get_object_or_404(Student, user=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, '个人信息更新成功！')
            return redirect('students:profile')
    else:
        form = StudentProfileForm(instance=student)
    
    # 获取练琴统计数据
    total_practice_time = PracticeRecord.objects.filter(
        student=student
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    # 从考勤应用获取考勤记录，而不是使用学生应用的Attendance模型
    from mymanage.attendance.models import AttendanceRecord
    
    # 获取考勤统计 - 使用AttendanceRecord模型
    total_attendance = AttendanceRecord.objects.filter(
        student=student,
        status='checked_out'  # 使用已签退的记录
    ).count()
    
    # 获取本月数据
    current_month = timezone.now().month
    current_year = timezone.now().year
    this_month_practice = PracticeRecord.objects.filter(
        student=student,
        date__month=current_month,
        date__year=current_year
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    # 计算最长练习时长
    max_practice_duration = PracticeRecord.objects.filter(
        student=student
    ).aggregate(max_duration=Max('duration'))['max_duration'] or 0
    
    # 计算平均每日练习时长
    avg_practice_duration = PracticeRecord.objects.filter(
        student=student
    ).aggregate(avg_duration=Avg('duration'))['avg_duration'] or 0
    
    # 获取最近7天的练习记录
    last_week_start = timezone.now().date() - timedelta(days=7)
    last_week_practice = PracticeRecord.objects.filter(
        student=student,
        date__gte=last_week_start
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    # 计算出勤率 - 使用AttendanceRecord模型
    # 总考勤记录数（包括所有状态）
    attendance_count = AttendanceRecord.objects.filter(student=student).count()
    attendance_rate = (total_attendance / attendance_count * 100) if attendance_count > 0 else 0
    
    # 获取学生所在课程信息
    from mymanage.courses.models import Course, CourseSchedule
    student_courses = Course.objects.filter(students=student)
    teacher_name = "未分配教师"
    course_type = "未分配课程"
    course_frequency = "未安排课程"
    class_times = []
    course_level = "未设置"
    
    # 如果有课程，获取第一个课程的信息
    if student_courses.exists():
        main_course = student_courses.first()
        teacher_name = main_course.teacher.name if main_course.teacher else "未分配教师"
        course_type = main_course.name
        
        # 获取课程级别
        course_level = main_course.level.get_level_display() if main_course.level else "未设置"
        
        # 课程安排
        schedules = CourseSchedule.objects.filter(course=main_course)
        course_frequency = f"每周{schedules.count()}次" if schedules.exists() else "未安排"
        
        # 课程时间
        for schedule in schedules:
            weekday_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
            weekday = weekday_map.get(schedule.weekday, "未知")
            start_time = schedule.start_time.strftime("%H:%M") if schedule.start_time else "00:00"
            end_time = schedule.end_time.strftime("%H:%M") if schedule.end_time else "00:00"
            class_times.append(f"{weekday} {start_time}-{end_time}")
    
    # 获取未读通知数量（如果有相关功能）
    notifications_count = 0  # 示例值，实际应从数据库查询
    
    # 获取考勤记录 - 使用AttendanceRecord模型
    attendance_records = AttendanceRecord.objects.filter(student=student).order_by('-check_in_time')[:5]
    
    # 获取练琴记录
    practice_records = PracticeRecord.objects.filter(student=student).order_by('-date', '-start_time')[:5]
    
    context = {
        'form': form,
        'student': student,
        'practice_records': practice_records,
        'attendances': attendance_records,
        'total_practice_time': total_practice_time,
        'total_attendance': total_attendance,
        'this_month_practice': this_month_practice,
        'max_practice_duration': max_practice_duration,
        'avg_practice_duration': round(avg_practice_duration, 1) if avg_practice_duration else 0,
        'last_week_practice': last_week_practice,
        'attendance_rate': round(attendance_rate, 1),
        'teacher_name': teacher_name,
        'course_type': course_type,
        'course_frequency': course_frequency,
        'class_times': ', '.join(class_times) if class_times else "未安排",
        'course_level': course_level,
        'notifications_count': notifications_count
    }
    return render(request, 'students/student_profile.html', context)

@login_required
def update_profile(request):
    student = get_object_or_404(Student, user=request.user)
    if request.method == 'POST':
        print(f"收到POST请求，FILES内容: {request.FILES}")
        print(f"请求内容类型: {request.META.get('CONTENT_TYPE', '未知')}")
        
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            
            # 处理头像上传
            if request.FILES and 'avatar' in request.FILES:
                avatar_file = request.FILES['avatar']
                print(f"接收到头像文件: {avatar_file.name}, 大小: {avatar_file.size} 字节")
                
                # 确保用户获取正确的引用
                user = request.user
                user.avatar = avatar_file
                user.save()
                
                # 输出保存后的路径
                print(f"头像已保存到: {user.avatar.path if user.avatar else '无路径'}")
                messages.success(request, f'个人信息和头像更新成功！头像大小: {avatar_file.size} 字节')
            else:
                print("请求中没有找到avatar文件")
                messages.success(request, '个人信息更新成功！但没有接收到头像文件')
            
            return redirect('students:profile')
        else:
            print(f"表单验证错误: {form.errors}")
            messages.error(request, f'表单验证错误: {form.errors}')
    else:
        form = StudentProfileForm(instance=student)
    
    context = {
        'form': form,
        'student': student
    }
    return render(request, 'students/student_profile_update.html', context)

@login_required
def practice(request):
    student = get_object_or_404(Student, user=request.user)
    today = timezone.now().date()
    current_time = timezone.now()
    
    # 自动清理异常状态的记录
    # 处理状态为active但已结束的记录
    expired_practices = PracticeRecord.objects.filter(
        student=student,
        end_time__lt=current_time,
        status='active'
    )
    
    if expired_practices.exists():
        for practice in expired_practices:
            practice.status = 'completed'
            practice.save()
            print(f"自动修复：练琴记录 {practice.id} 状态由active更新为completed")
    
    # 获取今日练琴记录(状态正确且未过期的)
    today_practice = PracticeRecord.objects.filter(
        student=student,
        date=today
    ).order_by('-start_time').first()
    
    # 确保如果有今日记录且状态为active，则end_time必须大于当前时间
    if today_practice and today_practice.status == 'active' and today_practice.end_time and today_practice.end_time <= current_time:
        today_practice.status = 'completed'
        today_practice.save()
        print(f"自动修复：当前显示的练琴记录 {today_practice.id} 状态由active更新为completed")
    
    # 获取当前正在使用的钢琴
    active_pianos = PracticeRecord.objects.filter(
        date=today,
        end_time__gt=current_time
    ).values_list('piano_number', flat=True)
    
    # 获取等待队列
    waiting_students = PracticeRecord.objects.filter(
        date=today,
        start_time__gt=current_time
    ).order_by('start_time')
    
    # 计算排队位置和预计等待时间
    waiting_position = 0
    estimated_wait_time = 0
    
    if today_practice and today_practice.start_time > current_time:
        # 学生在排队中
        waiting_position = list(waiting_students.values_list('id', flat=True)).index(today_practice.id) + 1
        # 预计等待时间（分钟）
        estimated_wait_time = (today_practice.start_time - current_time).total_seconds() // 60
    
    # 从数据库获取钢琴信息
    from mymanage.courses.models import Piano
    piano_brand = None
    piano_model = None
    
    if today_practice and today_practice.piano_number:
        piano_number = today_practice.piano_number
        try:
            # 尝试从Piano模型获取信息
            piano = Piano.objects.get(number=piano_number)
            piano_brand = piano.brand
            piano_model = piano.model
        except Piano.DoesNotExist:
            # 如果Piano模型中没有对应记录，使用默认值
            piano_brand = f"未知品牌-{piano_number}号"
            piano_model = "未知型号"
    
    # 获取通知数量
    # 未读通知的逻辑，如果有相关模型可以查询
    notifications_count = 0  # 示例值，实际应从数据库查询
    
    context = {
        'student': student,
        'today': today,
        'current_time': current_time,
        'today_practice': today_practice,
        'active_pianos': list(active_pianos),
        'waiting_students': waiting_students,
        'total_pianos': 7,
        'waiting_position': waiting_position,
        'estimated_wait_time': estimated_wait_time,
        'piano_brand': piano_brand,
        'piano_model': piano_model,
        'notifications_count': notifications_count
    }
    return render(request, 'students/student_practice.html', context)

@login_required
def check_in(request):
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        today = timezone.now().date()
        
        # 检查是否已经签到
        existing_attendance = Attendance.objects.filter(
            student=student,
            date=today
        ).first()
        
        if existing_attendance:
            return JsonResponse({
                'success': False,
                'message': '今天已经签到过了'
            })
        
        # 创建新的考勤记录
        attendance = Attendance.objects.create(
            student=student,
            date=today,
            check_in_time=timezone.now(),
            status='present'
        )
        
        # 导入Piano模型
        from mymanage.courses.models import Piano
        
        # 自动安排练琴时间
        active_practices = PracticeRecord.objects.filter(
            date=today,
            end_time__gt=timezone.now()
        )
        
        # 获取所有已分配的钢琴编号
        used_pianos = active_practices.values_list('piano_number', flat=True)
        
        # 查询所有可用的钢琴
        available_pianos = Piano.objects.filter(
            is_active=True, 
            is_occupied=False
        ).exclude(
            number__in=used_pianos
        ).order_by('number')
        
        if available_pianos.exists():
            # 有空闲钢琴，分配第一个可用的钢琴
            piano = available_pianos.first()
            
            # 标记钢琴为已占用
            piano.is_occupied = True
            piano.save()
            
            # 创建练琴记录
            next_practice = PracticeRecord.objects.create(
                student=student,
                date=today,
                start_time=timezone.now(),
                end_time=timezone.now() + timedelta(minutes=30),
                duration=30,
                piano_number=piano.number
            )
            
            return JsonResponse({
                'success': True,
                'message': '签到成功，已分配钢琴',
                'practice_time': next_practice.start_time.strftime('%H:%M'),
                'piano_number': piano.number,
                'piano_brand': piano.brand,
                'piano_model': piano.model,
                'waiting': False
            })
        else:
            # 所有钢琴都在使用中，安排等待
            # 找出最早结束的练琴记录
            earliest_end = active_practices.order_by('end_time').first()
            
            # 尝试获取对应的钢琴信息
            try:
                waiting_piano = Piano.objects.get(number=earliest_end.piano_number)
            except Piano.DoesNotExist:
                waiting_piano = None
            
            # 安排在这个时间之后
            start_time = earliest_end.end_time + timedelta(minutes=1)
            
            # 创建练琴记录（等待中）
            next_practice = PracticeRecord.objects.create(
                student=student,
                date=today,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=30),
                duration=30,
                piano_number=earliest_end.piano_number
            )
            
            # 计算等待时间（分钟）
            wait_minutes = (start_time - timezone.now()).total_seconds() // 60
            
            # 获取钢琴品牌和型号
            piano_brand = waiting_piano.brand if waiting_piano else f"未知品牌-{earliest_end.piano_number}号"
            piano_model = waiting_piano.model if waiting_piano else "未知型号"
            
            return JsonResponse({
                'success': True,
                'message': '签到成功，已加入等待队列',
                'practice_time': next_practice.start_time.strftime('%H:%M'),
                'piano_number': next_practice.piano_number,
                'piano_brand': piano_brand,
                'piano_model': piano_model,
                'waiting': True,
                'wait_minutes': int(wait_minutes)
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def check_out(request):
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        today = timezone.now().date()
        
        # 获取今日练琴记录
        practice = PracticeRecord.objects.filter(
            student=student,
            date=today,
            end_time__gt=timezone.now()
        ).first()
        
        if not practice:
            return JsonResponse({
                'success': False,
                'message': '没有找到进行中的练琴记录'
            })
        
        # 计算实际练琴时长
        now = timezone.now()
        actual_duration = (now - practice.start_time).total_seconds() // 60
        
        # 更新练琴记录
        practice.end_time = now
        practice.duration = actual_duration
        practice.save()
        
        # 释放钢琴
        from mymanage.courses.models import Piano
        try:
            piano = Piano.objects.get(number=practice.piano_number)
            piano.is_occupied = False
            piano.save()
        except Piano.DoesNotExist:
            # 如果钢琴不存在，仅记录日志，不中断流程
            print(f"警告: 无法找到编号为 {practice.piano_number} 的钢琴")
        
        # 更新考勤记录
        attendance = Attendance.objects.filter(
            student=student,
            date=today
        ).first()
        
        if attendance:
            attendance.check_out_time = now
            attendance.save()
        
        return JsonResponse({
            'success': True,
            'message': '签退成功，今日练琴时长：{} 分钟'.format(int(actual_duration))
        })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def scan_qrcode(request):
    """处理二维码扫描请求，支持GET和POST请求"""
    import logging
    logger = logging.getLogger(__name__)
    
    # 记录请求信息
    logger.debug(f"扫描二维码请求方法: {request.method}")
    if request.method == 'POST':
        logger.debug(f"POST数据: {request.POST}")
    
    # 获取请求参数
    session_id = request.GET.get('session_id') or request.POST.get('session_id')
    qrcode_data = request.POST.get('qrcode_data')
    
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({
            'success': False,
            'message': '只有学生用户可以扫描考勤码'
        }, status=400)
    
    student = request.user.student_profile
    logger.debug(f"处理学生ID: {student.id}, 姓名: {student.name}")
    
    # 导入所需模型
    from mymanage.attendance.models import AttendanceSession, AttendanceRecord, QRCode, WaitingQueue, PianoAssignment
    from mymanage.courses.models import Piano, Course
    
    # 处理特定会话ID的请求
    if session_id:
        logger.debug(f"使用会话ID处理: {session_id}")
        try:
            # 获取会话信息
            session = get_object_or_404(AttendanceSession, id=session_id)
            
            # 检查是否已有活跃的练琴记录
            active_practice = PracticeRecord.objects.filter(
                student=student,
                date=timezone.now().date(),
                status='active'
            ).first()
            
            if active_practice:
                # 计算已练习时间（分钟）
                elapsed_minutes = int((timezone.now() - active_practice.start_time).total_seconds() / 60)
                
                # 获取钢琴信息
                piano_number = active_practice.piano_number
                piano_brand = "未知"
                piano_model = "未知"
                
                try:
                    piano = Piano.objects.get(number=piano_number)
                    piano_brand = piano.brand
                    piano_model = piano.model
                except Piano.DoesNotExist:
                    pass
                
                return JsonResponse({
                    'success': True,
                    'message': f'您已在{piano_number}号钢琴练习中，已练习{elapsed_minutes}分钟',
                    'piano_number': piano_number,
                    'piano_brand': piano_brand,
                    'piano_model': piano_model,
                    'elapsed_minutes': elapsed_minutes,
                    'session_id': session.id,
                    'practice_id': active_practice.id
                })
            
            # 检查学生是否已有钢琴预留
            piano_assignment = PianoAssignment.objects.filter(
                session=session,
                student=student,
                status='reserved'
            ).first()
            
            # 如果已有钢琴预留，返回预留信息
            if piano_assignment:
                # 计算预留剩余时间
                remaining_seconds = (piano_assignment.expiration_time - timezone.now()).total_seconds()
                
                # 如果预留已过期但状态未更新，先更新状态
                if remaining_seconds <= 0:
                    piano_assignment.expire()
                    # 继续处理后续逻辑，检查是否有其他可用钢琴
                else:
                    remaining_minutes = round(remaining_seconds / 60, 1)
                    logger.info(f"找到钢琴预留: ID={piano_assignment.id}, 钢琴={piano_assignment.piano.number}, 剩余时间={remaining_minutes}分钟")
                    return JsonResponse({
                        'success': True,
                        'reserved': True,
                        'message': f'已为您预留{piano_assignment.piano.number}号钢琴，请在{remaining_minutes}分钟内点击"开始练琴"',
                        'piano_number': piano_assignment.piano.number,
                        'piano_brand': piano_assignment.piano.brand,
                        'piano_model': piano_assignment.piano.model,
                        'remaining_minutes': remaining_minutes,
                        'session_id': session.id,
                        'assignment_id': piano_assignment.id
                    })
            
            # 检查学生是否已在等待队列
            waiting_record = WaitingQueue.objects.filter(
                session=session,
                student=student,
                is_active=True
            ).first()
            
            # 如果已在等待队列中，返回等待信息
            if waiting_record:
                # 计算剩余等待时间
                total_wait_time = waiting_record.estimated_wait_time
                elapsed_minutes = int((timezone.now() - waiting_record.join_time).total_seconds() / 60)
                remaining_minutes = max(0, total_wait_time - elapsed_minutes)
                
                queue_position = WaitingQueue.objects.filter(
                    session=session,
                    is_active=True,
                    join_time__lt=waiting_record.join_time
                ).count() + 1
                
                logger.info(f"学生在等待队列中: ID={waiting_record.id}, 排队位置={queue_position}, 剩余时间={remaining_minutes}分钟")
                
                return JsonResponse({
                    'success': True,
                    'waiting': True,
                    'message': f'您已在等待队列中，预计还需等待{remaining_minutes}分钟',
                    'wait_minutes': remaining_minutes,
                    'queue_position': queue_position,
                    'session_id': session.id,
                    'waiting_id': waiting_record.id
                })
            
            # 清理过期的钢琴预留
            PianoAssignment.check_and_expire_reservations()
            
            # 查找可用的钢琴（未被占用且未被预留）
            available_pianos = Piano.objects.filter(
                is_active=True,
                is_occupied=False,
                is_reserved=False
            ).order_by('number')
            
            if available_pianos.exists():
                # 有空闲钢琴，但不立即预留，只返回可用信息
                available_count = available_pianos.count()
                logger.info(f"有{available_count}台可用钢琴")
                
                # 获取第一个可用钢琴信息用于显示
                piano = available_pianos.first()
                
                # 返回可用钢琴信息
                return JsonResponse({
                    'success': True,
                    'available_pianos': available_count,
                    'message': f'当前有{available_count}台可用钢琴，您可以点击"开始练琴"',
                    'piano_number': piano.number,  # 仅用于前端显示
                    'piano_brand': piano.brand,
                    'piano_model': piano.model,
                    'session_id': session.id
                })
            else:
                # 没有空闲钢琴，返回信息让前端提示加入等待队列
                logger.info("没有可用钢琴，返回等待队列信息")
                return JsonResponse({
                    'success': True,
                    'no_piano': True,
                    'message': '当前没有可用的钢琴，请加入等待队列',
                    'session_id': session.id
                })
                
        except Exception as e:
            import traceback
            logger.error(f"处理会话时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'处理会话时出错: {str(e)}'
            }, status=500)
    
    # 处理二维码数据
    elif qrcode_data:
        logger.debug(f"使用二维码数据处理: {qrcode_data}")
        try:
            # 去除可能存在的引号和首尾空格
            qrcode_data = qrcode_data.strip().strip('"\'')
            logger.debug(f"处理后的二维码数据: {qrcode_data}")
            
            # 导入UUID模块
            import uuid
            from django.core.exceptions import ObjectDoesNotExist
            
            qrcode_obj = None
            
            try:
                # 尝试作为UUID字符串查找
                uuid_obj = uuid.UUID(qrcode_data)
                qrcode_obj = QRCode.objects.filter(uuid=uuid_obj).first()
                logger.debug(f"通过UUID查找结果: {qrcode_obj}")
                
                # 如果没找到，尝试通过code字段查找
                if not qrcode_obj:
                    qrcode_obj = QRCode.objects.filter(code=qrcode_data).first()
                    logger.debug(f"通过code字段查找结果: {qrcode_obj}")
            except ValueError:
                # 不是有效的UUID，尝试通过code字段查找
                qrcode_obj = QRCode.objects.filter(code=qrcode_data).first()
                logger.debug(f"非UUID格式，通过code字段查找结果: {qrcode_obj}")
            
            # 如果找到有效的二维码
            if qrcode_obj:
                logger.debug(f"找到二维码: ID={qrcode_obj.id}, 过期时间={qrcode_obj.expires_at}")
                
                # 检查二维码是否有效
                if not qrcode_obj.is_valid():
                    logger.debug(f"二维码已过期: {qrcode_obj.expires_at} < {timezone.now()}")
                    return JsonResponse({
                        'success': False,
                        'message': '二维码已过期'
                    }, status=400)
                
                # 获取关联的考勤会话
                session = AttendanceSession.objects.filter(qrcode=qrcode_obj, status='active').first()
                
                if not session:
                    # 尝试查找相关联的会话
                    related_sessions = AttendanceSession.objects.filter(
                        qrcode=qrcode_obj
                    ).order_by('-start_time')
                    
                    if related_sessions.exists():
                        # 找到了会话，但不是active状态
                        related_session = related_sessions.first()
                        logger.debug(f"找到相关会话但状态非活跃: ID={related_session.id}, 状态={related_session.status}")
                        
                        if related_session.status == 'closed':
                            return JsonResponse({
                                'success': False,
                                'message': '考勤会话已关闭，请联系老师'
                            }, status=400)
                    
                    # 没有找到会话，使用二维码创建一个新的临时会话
                    logger.debug(f"未找到会话，创建新会话")
                    try:
                        session = AttendanceSession.objects.create(
                            course=qrcode_obj.course,
                            qrcode=qrcode_obj,
                            created_by=request.user,
                            start_time=timezone.now(),
                            status='active',
                            is_active=True,
                            description=f"通过二维码创建的临时会话 - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                        logger.debug(f"成功创建新会话: ID={session.id}")
                    except Exception as e:
                        logger.error(f"创建新会话失败: {str(e)}")
                        return JsonResponse({
                            'success': False,
                            'message': f'无法创建考勤会话: {str(e)}'
                        }, status=400)
                
                # 递归调用自身，使用找到的会话ID处理
                logger.debug(f"使用会话ID: {session.id} 重新处理请求")
                request.method = 'GET'  # 强制使用GET方法
                request.GET = request.GET.copy()
                request.GET['session_id'] = str(session.id)
                return scan_qrcode(request)
            else:
                # 二维码未找到
                logger.warning(f"未找到匹配的二维码: {qrcode_data}")
                return JsonResponse({
                    'success': False,
                    'message': '无效的二维码或二维码已过期'
                }, status=400)
        
        except Exception as e:
            import traceback
            logger.error(f"处理二维码数据时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'处理二维码时出错: {str(e)}'
            }, status=500)
    
    else:
        # 缺少必要参数
        logger.warning("请求缺少必要参数")
        return JsonResponse({
            'success': False,
            'message': '请求参数不足，需要提供二维码数据或会话ID'
        }, status=400)

@login_required
def start_practice(request):
    """开始练琴，创建练琴记录"""
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        student = Student.objects.get(user=request.user)
        session_id = request.POST.get('session_id')
        assignment_id = request.POST.get('assignment_id')
        
        logger.info(f"开始练琴请求 - 学生: {student.name}, 会话ID: {session_id}, 预留ID: {assignment_id}")
        
        try:
            from mymanage.attendance.models import AttendanceSession, AttendanceRecord, PianoAssignment
            from mymanage.courses.models import Piano
            
            # 获取会话信息
            session = get_object_or_404(AttendanceSession, id=session_id)
            
            # 检查是否已有活跃的练琴记录
            active_practice = PracticeRecord.objects.filter(
                student=student,
                date=timezone.now().date(),
                status='active'
            ).first()
            
            if active_practice:
                logger.info(f"学生已有活跃练琴记录，无法重复开始: ID={active_practice.id}")
                
                # 获取钢琴信息
                piano_number = active_practice.piano_number
                piano_brand = "未知"
                piano_model = "未知"
                
                try:
                    piano = Piano.objects.get(number=piano_number)
                    piano_brand = piano.brand
                    piano_model = piano.model
                except Piano.DoesNotExist:
                    pass
                
                # 返回已有的练琴记录
                return JsonResponse({
                    'success': True,
                    'message': f'您已在{piano_number}号钢琴练习中',
                    'practice_id': active_practice.id,
                    'piano_number': piano_number,
                    'piano_brand': piano_brand,
                    'piano_model': piano_model
                })
            
            # 查找预留信息
            piano_assignment = None
            if assignment_id:
                try:
                    piano_assignment = PianoAssignment.objects.get(
                        id=assignment_id,
                        student=student,
                        status='reserved'
                    )
                    # 检查预留是否已过期
                    if piano_assignment.is_expired():
                        piano_assignment.expire()
                        piano_assignment = None
                        logger.info(f"钢琴预留已过期，无法使用")
                except PianoAssignment.DoesNotExist:
                    logger.info(f"找不到钢琴预留: ID={assignment_id}")
                    piano_assignment = None
            
            # 获取钢琴
            piano = None
            
            # 如果有预留的钢琴，使用该钢琴
            if piano_assignment:
                piano = piano_assignment.piano
                # 将预留状态更新为已分配
                piano_assignment.assign()
                logger.info(f"将预留钢琴分配给学生: 钢琴={piano.number}, 学生={student.name}")
            else:
                # 没有预留，直接查找可用钢琴
                available_pianos = Piano.objects.filter(
                    is_active=True, 
                    is_occupied=False, 
                    is_reserved=False
                ).order_by('number')
                
                if available_pianos.exists():
                    piano = available_pianos.first()
                    # 立即占用钢琴
                    piano.start_using()
                    logger.info(f"无预留情况下为学生分配钢琴：{piano.number}")
                else:
                    # 检查学生是否已在等待队列
                    from mymanage.attendance.models import WaitingQueue
                    waiting_record = WaitingQueue.objects.filter(
                        session=session,
                        student=student,
                        is_active=True
                    ).first()
                    
                    # 无钢琴可用，建议加入等待队列
                    if not waiting_record:
                        return JsonResponse({
                            'success': False,
                            'no_piano': True,
                            'message': '当前没有可用的钢琴，请加入等待队列',
                            'session_id': session_id
                        })
                    else:
                        # 已在等待队列，返回队列信息
                        queue_position = WaitingQueue.objects.filter(
                            session=session,
                            is_active=True,
                            join_time__lt=waiting_record.join_time
                        ).count() + 1
                        
                        elapsed_minutes = int((timezone.now() - waiting_record.join_time).total_seconds() / 60)
                        remaining_minutes = max(0, waiting_record.estimated_wait_time - elapsed_minutes)
                        
                        return JsonResponse({
                            'success': False,
                            'waiting': True,
                            'message': f'您需要等待钢琴，当前排队位置：{queue_position}，预计等待时间：{remaining_minutes}分钟',
                            'queue_position': queue_position,
                            'wait_minutes': remaining_minutes,
                            'waiting_id': waiting_record.id,
                            'session_id': session_id
                        })
            
            # 创建练琴记录
            start_time = timezone.now()
            end_time = start_time + timezone.timedelta(hours=2)  # 默认2小时后结束
            
            practice = PracticeRecord.objects.create(
                student=student,
                date=start_time.date(),
                piano_number=piano.number,
                start_time=start_time,
                end_time=end_time,
                status='active',
                attendance_session=session  # 关联考勤会话
            )
            
            logger.info(f"创建新的练琴记录: ID={practice.id}, 日期={practice.date}, 钢琴={piano.number}")
            
            # 同时创建或更新考勤记录
            try:
                # 检查是否已有考勤记录
                att_record = AttendanceRecord.objects.filter(
                    session=session,
                    student=student
                ).first()
                
                if not att_record:
                    # 创建新的考勤记录
                    AttendanceRecord.objects.create(
                        session=session,
                        student=student,
                        piano=piano,
                        check_in_time=start_time,
                        status='checked_in'
                    )
                    logger.info(f"创建新的考勤记录，学生={student.name}, 钢琴={piano.number}")
                else:
                    # 更新现有考勤记录
                    att_record.piano = piano
                    att_record.check_in_time = start_time
                    att_record.status = 'checked_in'
                    att_record.save()
                    logger.info(f"更新考勤记录: ID={att_record.id}, 钢琴={piano.number}")
            except Exception as e:
                logger.error(f"创建/更新考勤记录时出错: {str(e)}")
            
            # 同时创建旧版Attendance模型记录（仅为兼容）
            try:
                # 检查是否已有旧版考勤记录
                old_attendance = Attendance.objects.filter(
                    student=student,
                    date=start_time.date()
                ).first()
                
                if not old_attendance:
                    Attendance.objects.create(
                        student=student,
                        date=start_time.date(),
                        check_in_time=start_time,
                        status='present'
                    )
                    logger.info(f"创建兼容性旧版考勤记录，日期={start_time.date()}")
            except Exception as e:
                logger.error(f"创建旧版考勤记录时出错: {str(e)}")
            
            # 返回成功信息
            return JsonResponse({
                'success': True,
                'message': f'已开始在{piano.number}号钢琴练习',
                'practice_id': practice.id,
                'piano_number': piano.number,
                'piano_brand': piano.brand,
                'piano_model': piano.model
            })
            
        except Exception as e:
            import traceback
            logger.error(f"开始练琴时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'开始练琴时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def check_waiting_status(request):
    """检查学生在等待队列中的状态"""
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'GET':
        waiting_id = request.GET.get('waiting_id')
        if not waiting_id:
            return JsonResponse({
                'success': False,
                'message': '缺少等待ID'
            })
        
        try:
            from mymanage.attendance.models import WaitingQueue, AttendanceRecord, PianoAssignment
            from mymanage.courses.models import Piano
            
            waiting = get_object_or_404(WaitingQueue, id=waiting_id)
            student = waiting.student
            
            # 如果不再活跃，表示可能已被分配钢琴
            if not waiting.is_active:
                # 检查是否有钢琴预留
                piano_assignment = PianoAssignment.objects.filter(
                    student=student,
                    session=waiting.session,
                    status='reserved'
                ).first()
                
                if piano_assignment and not piano_assignment.is_expired():
                    # 有钢琴预留，返回预留信息
                    piano = piano_assignment.piano
                    remaining_seconds = (piano_assignment.expiration_time - timezone.now()).total_seconds()
                    remaining_minutes = max(0, round(remaining_seconds / 60, 1))
                    
                    logger.info(f"等待学生已被分配钢琴: 学生={student.name}, 钢琴={piano.number}, 剩余预留时间={remaining_minutes}分钟")
                    
                    return JsonResponse({
                        'success': True,
                        'ready': True,
                        'message': f'您可以开始练琴，已为您预留{piano.number}号钢琴，请在{remaining_minutes}分钟内点击"开始练琴"',
                        'piano_number': piano.number,
                        'piano_brand': piano.brand,
                        'piano_model': piano.model,
                        'session_id': waiting.session.id,
                        'assignment_id': piano_assignment.id,
                        'remaining_minutes': remaining_minutes
                    })
                
                # 检查是否已有考勤记录和分配的钢琴
                attendance = AttendanceRecord.objects.filter(
                    student=student,
                    session=waiting.session,
                    status='checked_in'
                ).first()
                
                if attendance and attendance.piano:
                    # 已分配钢琴并已签到
                    return JsonResponse({
                        'success': True,
                        'ready': True,
                        'message': f'您可以开始练琴，已为您分配{attendance.piano.number}号钢琴',
                        'piano_number': attendance.piano.number,
                        'piano_brand': attendance.piano.brand,
                        'piano_model': attendance.piano.model,
                        'session_id': waiting.session.id
                    })
                else:
                    # 等待状态已结束但未分配钢琴
                    return JsonResponse({
                        'success': True,
                        'ready': False,
                        'message': '您的等待已结束，但尚未分配钢琴，请重新扫码',
                        'session_id': waiting.session.id
                    })
            
            # 计算剩余等待时间
            if waiting.practice_record:
                # 如果已经分配了练琴记录，基于练琴记录计算
                if waiting.practice_record.status == 'active':
                    # 如果正在练琴，显示剩余练琴时间
                    remaining_minutes = max(0, int((waiting.practice_record.end_time - timezone.now()).total_seconds() / 60))
                else:
                    # 如果还没开始练琴，显示等待时间
                    remaining_minutes = max(0, int((waiting.practice_record.start_time - timezone.now()).total_seconds() / 60))
            else:
                # 如果还没分配练琴记录，重新计算等待时间
                active_practices = PracticeRecord.objects.filter(
                    date=timezone.now().date(),
                    status='active'
                ).order_by('end_time')
                
                if active_practices.exists():
                    earliest_available_time = active_practices.first().end_time
                    wait_minutes = max(0, int((earliest_available_time - timezone.now()).total_seconds() / 60))
                    queue_position = WaitingQueue.objects.filter(
                        session=waiting.session,
                        is_active=True,
                        join_time__lte=waiting.join_time
                    ).count()
                    remaining_minutes = wait_minutes + ((queue_position - 1) * 5)
                else:
                    queue_position = WaitingQueue.objects.filter(
                        session=waiting.session,
                        is_active=True,
                        join_time__lte=waiting.join_time
                    ).count()
                    remaining_minutes = 5 + ((queue_position - 1) * 5)
            
            # 更新等待记录的预计等待时间
            waiting.estimated_wait_time = remaining_minutes
            waiting.save()
            
            # 获取当前队列位置
            queue_position = WaitingQueue.objects.filter(
                session=waiting.session,
                is_active=True,
                join_time__lt=waiting.join_time
            ).count() + 1
            
            # 检查是否有空闲钢琴，并且是队列中第一位
            available_pianos = Piano.objects.filter(
                is_active=True,
                is_occupied=False,
                is_reserved=False
            )
            
            if available_pianos.exists() and queue_position <= 1:
                # 为该学生预留钢琴
                piano = available_pianos.first()
                
                # 预留时间为30秒
                reservation_time = 0.5  # 30秒
                
                # 标记等待状态为非活跃
                waiting.is_active = False
                waiting.save()
                
                # 为学生预留钢琴
                piano.reserve_for_student(student, minutes=reservation_time)
                
                # 创建预留记录
                expiration_time = timezone.now() + timezone.timedelta(minutes=reservation_time)
                assignment = PianoAssignment.objects.create(
                    session=waiting.session,
                    student=student,
                    piano=piano,
                    expiration_time=expiration_time,
                    status='reserved'
                )
                
                logger.info(f"为等待队列中的学生预留钢琴: 学生={student.name}, 钢琴={piano.number}, 预留时间={reservation_time}分钟")
                
                return JsonResponse({
                    'success': True,
                    'ready': True,
                    'message': f'有钢琴可用！已为您预留{piano.number}号钢琴，请在{int(reservation_time*60)}秒内点击"开始练琴"',
                    'piano_number': piano.number,
                    'piano_brand': piano.brand,
                    'piano_model': piano.model,
                    'session_id': waiting.session.id,
                    'assignment_id': assignment.id,
                    'remaining_minutes': reservation_time
                })
            
            # 仍在等待中
            return JsonResponse({
                'success': True,
                'waiting': True,
                'message': f'您仍在等待队列中，当前排队位置：{queue_position}，预计还需等待{remaining_minutes}分钟',
                'queue_position': queue_position,
                'wait_minutes': remaining_minutes,
                'session_id': waiting.session.id,
                'waiting_id': waiting.id
            })
            
        except Exception as e:
            import traceback
            logger.error(f"检查等待状态时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'检查等待状态时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def join_waiting_queue(request):
    """加入等待队列"""
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        student = Student.objects.get(user=request.user)
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': '缺少会话ID'
            })
        
        try:
            from mymanage.attendance.models import AttendanceSession, WaitingQueue, PianoAssignment
            from mymanage.courses.models import Piano
            
            # 检查会话是否存在
            session = get_object_or_404(AttendanceSession, id=session_id)
            
            # 检查是否已经在队列中
            existing_queue = WaitingQueue.objects.filter(
                session=session,
                student=student,
                is_active=True
            ).first()
            
            # 如果已在队列中，直接返回信息
            if existing_queue:
                # 计算剩余等待时间
                total_wait_time = existing_queue.estimated_wait_time
                elapsed_minutes = int((timezone.now() - existing_queue.join_time).total_seconds() / 60)
                remaining_minutes = max(0, total_wait_time - elapsed_minutes)
                
                queue_position = WaitingQueue.objects.filter(
                    session=session,
                    is_active=True,
                    join_time__lt=existing_queue.join_time
                ).count() + 1
                
                return JsonResponse({
                    'success': True,
                    'message': f'您已在等待队列中，预计还需等待{remaining_minutes}分钟',
                    'wait_minutes': remaining_minutes,
                    'queue_position': queue_position,
                    'waiting_id': existing_queue.id
                })
            
            # 再次检查是否有空闲钢琴，优先直接分配
            Piano.check_and_expire_reservations()  # 先清理过期的预留
            
            available_pianos = Piano.objects.filter(
                is_active=True,
                is_occupied=False,
                is_reserved=False
            ).order_by('number')
            
            if available_pianos.exists():
                # 有空闲钢琴，不需要加入等待队列，返回可用信息
                piano = available_pianos.first()
                available_count = available_pianos.count()
                
                return JsonResponse({
                    'success': True,
                    'available_pianos': available_count,
                    'message': f'有{available_count}台空闲钢琴可用，您可以直接开始练琴',
                    'piano_number': piano.number,
                    'piano_brand': piano.brand,
                    'piano_model': piano.model,
                    'session_id': session.id
                })
            
            # 计算预计等待时间
            # 1. 获取所有正在练琴的记录
            active_practices = PracticeRecord.objects.filter(
                date=timezone.now().date(),
                status='active'
            ).order_by('end_time')
            
            # 2. 计算最早可用的钢琴时间
            earliest_available_time = None
            if active_practices.exists():
                earliest_available_time = active_practices.first().end_time
            
            # 3. 计算等待队列长度
            queue_length = WaitingQueue.objects.filter(
                session=session,
                is_active=True
            ).count()
            
            # 4. 计算预计等待时间
            if earliest_available_time:
                # 如果有正在练琴的记录，基于最早结束时间计算
                wait_minutes = max(0, int((earliest_available_time - timezone.now()).total_seconds() / 60))
                # 加上队列位置的影响（每人在队列中增加5分钟）
                estimated_wait_time = wait_minutes + (queue_length * 5)
            else:
                # 如果没有正在练琴的记录，使用基础等待时间
                estimated_wait_time = 5 + (queue_length * 5)
            
            # 创建等待队列记录
            waiting_record = WaitingQueue.objects.create(
                session=session,
                student=student,
                estimated_wait_time=estimated_wait_time
            )
            
            # 队列位置是新记录在队列中的位置
            queue_position = queue_length + 1
            
            logger.info(f"学生{student.name}加入等待队列，位置：{queue_position}，预计等待时间：{estimated_wait_time}分钟")
            
            # 返回等待信息
            return JsonResponse({
                'success': True,
                'message': f'已加入等待队列，当前排队位置：{queue_position}，预计等待时间：{estimated_wait_time}分钟',
                'wait_minutes': estimated_wait_time,
                'queue_position': queue_position,
                'waiting_id': waiting_record.id
            })
            
        except Exception as e:
            import traceback
            logger.error(f"加入等待队列时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'加入等待队列时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def end_practice(request):
    """结束练琴函数"""
    if request.method == 'POST':
        practice_id = request.POST.get('practice_id')
        
        if not practice_id:
            return JsonResponse({
                'success': False,
                'message': '缺少练习ID'
            })
        
        try:
            from mymanage.courses.models import Piano
            from mymanage.attendance.models import AttendanceRecord
            import logging
            
            # 获取日志记录器
            logger = logging.getLogger(__name__)
            logger.info(f"收到结束练琴请求: 练习ID={practice_id}")
            
            # 获取练习记录
            practice = get_object_or_404(PracticeRecord, id=practice_id)
            
            # 检查是否是本人的练习记录
            if practice.student.user != request.user:
                return JsonResponse({
                    'success': False,
                    'message': '无权结束此练习记录'
                })
            
            # 如果记录已经结束，直接返回成功
            if practice.status != 'active':
                return JsonResponse({
                    'success': True,
                    'message': '练习已经结束'
                })
            
            current_time = timezone.now()
            
            # 计算练习时长（分钟）
            duration_minutes = int((current_time - practice.start_time).total_seconds() / 60)
            
            # 更新练习记录
            practice.status = 'completed'
            practice.end_time = current_time
            practice.duration = duration_minutes
            practice.save()
            
            # 释放钢琴
            try:
                piano = Piano.objects.get(number=practice.piano_number)
                # 检查是否有其他学生正在使用此钢琴
                other_records = PracticeRecord.objects.filter(
                    piano_number=practice.piano_number,
                    status='active'
                ).exclude(id=practice.id).exists()
                
                # 只有在没有其他记录的情况下才释放钢琴
                if not other_records:
                    piano.is_occupied = False
                    piano.save()
                    logger.info(f"钢琴已释放: 编号={piano.number}")
                else:
                    logger.info(f"钢琴仍有其他学生使用，保持占用状态: 编号={piano.number}")
            except Piano.DoesNotExist:
                logger.warning(f"找不到钢琴: 编号={practice.piano_number}")
            
            # 更新考勤记录
            if practice.attendance_session:
                attendance = AttendanceRecord.objects.filter(
                    session=practice.attendance_session,
                    student=practice.student,
                    status='checked_in'
                ).first()
                
                if attendance:
                    attendance.check_out_time = current_time
                    attendance.status = 'checked_out'
                    attendance.duration_minutes = duration_minutes
                    attendance.duration = duration_minutes / 60
                    attendance.save()
                    logger.info(f"考勤记录已更新为签退状态: ID={attendance.id}")
            
            # 更新旧版考勤记录（兼容性）
            try:
                old_attendance = Attendance.objects.filter(
                    student=practice.student,
                    date=practice.date,
                    status='present'
                ).first()
                
                if old_attendance and not old_attendance.check_out_time:
                    old_attendance.check_out_time = current_time
                    old_attendance.save()
                    logger.info(f"旧版考勤记录已更新: ID={old_attendance.id}")
            except Exception as e:
                logger.error(f"更新旧版考勤记录时出错: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'message': f'练习已结束，共练习{duration_minutes}分钟',
                'duration': duration_minutes
            })
            
        except Exception as e:
            import traceback
            logger.error(f"结束练琴时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'结束练琴时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def check_practice_status(request):
    """检查学生练琴状态"""
    if request.method == 'GET':
        practice_id = request.GET.get('practice_id')
        if not practice_id:
            return JsonResponse({
                'success': False,
                'message': '缺少练琴ID'
            })
        
        try:
            from mymanage.attendance.models import PracticeRecord
            from mymanage.courses.models import Piano
            
            practice = get_object_or_404(PracticeRecord, id=practice_id)
            
            # 检查是否是当前学生的练琴记录
            if practice.student.user != request.user:
                return JsonResponse({
                    'success': False,
                    'message': '无权查看此练琴记录'
                })
            
            # 获取钢琴信息
            piano_number = practice.piano_number
            piano_brand = "未知"
            piano_model = "未知"
            
            if piano_number:
                try:
                    piano = Piano.objects.get(number=piano_number)
                    piano_brand = piano.brand
                    piano_model = piano.model
                except Piano.DoesNotExist:
                    print(f"警告：练琴记录关联的钢琴 {piano_number} 不存在")
            
            # 计算练习时长（精确到秒）
            current_time = timezone.now()
            
            if practice.status == 'active':
                elapsed_seconds = int((current_time - practice.start_time).total_seconds())
                elapsed_minutes = elapsed_seconds // 60
                remaining_seconds = elapsed_seconds % 60
                
                # 检查是否练琴时间已超过30分钟
                can_checkout = elapsed_minutes >= 30
                
                return JsonResponse({
                    'success': True,
                    'status': 'active',
                    'elapsed_minutes': elapsed_minutes,
                    'elapsed_seconds': remaining_seconds,
                    'total_seconds': elapsed_seconds,
                    'start_time': practice.start_time.isoformat(),
                    'piano_number': piano_number,
                    'piano_brand': piano_brand,
                    'piano_model': piano_model,
                    'practice_id': practice.id,
                    'can_checkout': can_checkout,
                    'message': f'练琴进行中，已练习{elapsed_minutes}分{remaining_seconds}秒'
                })
            elif practice.status == 'completed':
                # 计算实际练习时长
                if practice.end_time and practice.start_time:
                    duration_seconds = int((practice.end_time - practice.start_time).total_seconds())
                    duration_minutes = duration_seconds // 60
                    duration_seconds_remainder = duration_seconds % 60
                else:
                    duration_seconds = 0
                    duration_minutes = 0
                    duration_seconds_remainder = 0
                
                return JsonResponse({
                    'success': True,
                    'status': 'completed',
                    'elapsed_minutes': duration_minutes,
                    'elapsed_seconds': duration_seconds_remainder,
                    'total_seconds': duration_seconds,
                    'piano_number': piano_number,
                    'piano_brand': piano_brand,
                    'piano_model': piano_model,
                    'message': f'练琴已完成，总练习时长{duration_minutes}分{duration_seconds_remainder}秒'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'status': 'inactive',
                    'message': '练琴记录未激活'
                })
        
        except Exception as e:
            import traceback
            print(f"检查练琴状态时出错: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'检查练琴状态时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def attendance(request):
    student = get_object_or_404(Student, user=request.user)
    today = timezone.now().date()
    
    # 直接使用PracticeRecord作为考勤记录
    from django.db.models import Count, Sum, F, Avg, ExpressionWrapper, DurationField
    from django.db.models.functions import TruncMonth, Extract
    import calendar, traceback
    
    try:
        print(f"开始获取考勤记录 - 学生: {student.name}, 日期: {today}")
        print(f"学生ID: {student.id}, 用户ID: {student.user_id}")
        
        # 获取进行中的练琴记录
        active_practice = PracticeRecord.objects.filter(
            student=student,
            date=today,
            status='active'
        ).first()
        
        if active_practice:
            print(f"找到进行中的练琴记录: ID={active_practice.id}, 开始时间={active_practice.start_time}")
        
        # 获取今日或最新的已完成练琴记录
        today_attendance = PracticeRecord.objects.filter(
            student=student,
            date=today,
            status='completed'
        ).order_by('-end_time').first()
        
        if not today_attendance:
            # 如果今天没有已完成记录，获取最近的一条完成记录
            today_attendance = PracticeRecord.objects.filter(
                student=student,
                status='completed'
            ).order_by('-date', '-end_time').first()
            
            if today_attendance:
                print(f"找到最近练琴记录: ID={today_attendance.id}, 日期={today_attendance.date}, "
                      f"时长={today_attendance.duration}分钟")
        else:
            print(f"找到今日练琴记录: ID={today_attendance.id}, 时长={today_attendance.duration}分钟")
        
        # 获取所有练琴记录作为考勤记录（包含已完成和进行中的）
        attendances = PracticeRecord.objects.filter(
            student=student
        ).filter(
            Q(status='completed') | Q(status='active')
        ).order_by('-date', '-start_time')
        
        # 分页 - 修改为每页5条
        paginator = Paginator(attendances, 5)
        page = request.GET.get('page')
        attendances_page = paginator.get_page(page)
        
        # 计算出勤率 - 当月计算
        current_month = today.month
        current_year = today.year
        
        # 获取当月的天数
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        
        # 计算到今天为止的天数
        days_so_far = today.day
        
        # 获取最近7天的不同练琴日期数量
        week_start = today - timezone.timedelta(days=6)  # 一周前
        distinct_practice_days = PracticeRecord.objects.filter(
            student=student,
            date__gte=week_start,
            date__lte=today
        ).filter(
            Q(status='completed') | Q(status='active')
        ).values('date').distinct().count()
        
        # 计算出勤率 - 最近7天的不同练琴日期数 / 7天
        attendance_rate = (distinct_practice_days / 7 * 100)
        
        # 为了调试输出相关信息
        print(f"计算周期: {week_start.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}")
        print(f"本周不同练琴日期数: {distinct_practice_days}天")
        print(f"本周出勤率: {attendance_rate:.2f}%")
        
        # 获取练琴统计数据
        total_practice_time = attendances.filter(status='completed').aggregate(
            total=Sum('duration')
        )['total'] or 0
        
        # 获取练琴时长统计 - 平均每次练习时长
        avg_practice_time = attendances.filter(
            status='completed',
            duration__isnull=False
        ).aggregate(
            avg=Avg('duration')
        )['avg'] or 0
        
        # 获取最长练习记录
        longest_practice = attendances.filter(status='completed').order_by('-duration').first()
        max_practice_time = longest_practice.duration if longest_practice else 0
        
        # 获取最近练琴记录 - 包含详细信息
        recent_practices = attendances.order_by('-date', '-start_time')[:5]
        
        # 创建日历数据 - 对最近3个月的数据进行处理
        three_months_ago = timezone.now() - timezone.timedelta(days=90)
        calendar_data = []
        
        calendar_records = attendances.filter(
            date__gte=three_months_ago.date()
        )
        
        for record in calendar_records:
            # 根据练琴状态设置事件类型和颜色
            event_class = 'practice-event' 
            
            if record.status == 'active':
                # 计算已进行时长
                elapsed_minutes = int((timezone.now() - record.start_time).total_seconds() / 60)
                title = f'练琴中 {elapsed_minutes}分钟'
                event_color = '#ffc107'  # 黄色
            elif record.status == 'completed':
                title = f'练琴 {int(record.duration) if record.duration else 0} 分钟'
                event_color = '#28a745'  # 绿色
            else:
                title = record.status
                event_color = '#6c757d'  # 灰色
            
            calendar_data.append({
                'title': title,
                'start': record.date.strftime('%Y-%m-%d'),
                'className': event_class,
                'color': event_color
            })
        
        # 将日历数据转换为JSON格式
        calendar_json = json.dumps(calendar_data)
        
        # 计算累计考勤天数 - 使用去重后的日期数量
        total_attendance_days = PracticeRecord.objects.filter(
            student=student,
            status='completed'
        ).values('date').distinct().count()
        
        print(f"累计考勤天数: {total_attendance_days}天")
        
        # 组装上下文数据
        context = {
            'student': student,
            'today_attendance': today_attendance,
            'active_practice': active_practice,  # 添加当前正在进行的练琴记录
            'attendances': attendances_page,
            'total_days': total_attendance_days,  # 实际考勤天数，使用去重后的日期数量
            'present_days': distinct_practice_days,  # 本周签到记录数
            'attendance_rate': attendance_rate,
            'total_practice_time': round(total_practice_time / 60, 1),  # 将分钟转换为小时并保留一位小数
            'avg_practice_time': round(avg_practice_time, 1),
            'max_practice_time': max_practice_time,
            'calendar_data': calendar_json,
            'recent_practices': recent_practices
        }
        
        return render(request, 'students/student_attendance.html', context)
    except Exception as e:
        print(f"加载考勤页面时出错: {str(e)}")
        traceback.print_exc()
        messages.error(request, f"加载考勤页面时出错: {str(e)}")
        
        # 返回一个简单的错误页面，确保提供basic context
        context = {
            'student': student,
            'error_message': str(e),
            'today_attendance': None,
            'active_practice': None,
            'attendances': [],
            'attendance_rate': 0,
            'total_practice_time': 0,
            'avg_practice_time': 0,
            'max_practice_time': 0,
            'calendar_data': '[]',
            'recent_practices': [],
            'total_days': 0
        }
        return render(request, 'students/student_attendance.html', context)

@login_required
def attendance_history(request):
    """获取考勤历史数据"""
    student = get_object_or_404(Student, user=request.user)
    
    # 使用PracticeRecord作为考勤记录
    attendances = PracticeRecord.objects.filter(
        student=student,
        status='completed'  # 只获取已完成的记录
    ).order_by('-date', '-end_time')
    
    # 分页处理
    paginator = Paginator(attendances, 10)
    page = request.GET.get('page')
    attendances = paginator.get_page(page)
    
    context = {
        'student': student,
        'attendances': attendances
    }
    
    return render(request, 'students/student_attendance_history.html', context)

@login_required
def attendance_stats(request):
    """获取考勤统计数据"""
    student = get_object_or_404(Student, user=request.user)
    
    # 获取月度考勤统计
    now = timezone.now()
    months = []
    for i in range(6):
        month = now.month - i if now.month - i > 0 else now.month - i + 12
        year = now.year if now.month - i > 0 else now.year - 1
        
        month_count = PracticeRecord.objects.filter(
            student=student,
            date__month=month,
            date__year=year,
            status='completed'
        ).count()
        
        months.append({
            'month': f'{year}年{month}月',
            'count': month_count
        })
    
    months.reverse()
    
    # 获取每周统计
    weeks = []
    for i in range(4):
        start_date = now - timedelta(days=now.weekday() + 7 * i)
        end_date = start_date + timedelta(days=6)
        
        week_count = PracticeRecord.objects.filter(
            student=student,
            date__gte=start_date,
            date__lte=end_date,
            status='completed'
        ).count()
        
        weeks.append({
            'week': f'第{i+1}周',
            'count': week_count
        })
    
    weeks.reverse()
    
    return JsonResponse({
        'success': True,
        'months': months,
        'weeks': weeks
    })

@login_required
def attendance_calendar_data(request):
    """获取日历显示的考勤数据"""
    student = get_object_or_404(Student, user=request.user)
    
    # 获取查询的年月
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)
    
    # 查询该月的所有练琴记录
    practices = PracticeRecord.objects.filter(
        student=student,
        date__year=year,
        date__month=month
    )
    
    # 格式化为日历事件
    events = []
    for practice in practices:
        # 根据练琴记录状态设置显示颜色
        if practice.status == 'active':
            title = '练琴中'
            color = '#FFC107'  # 黄色
        elif practice.status == 'completed':
            title = f'练琴 {int(practice.duration) if practice.duration else 0} 分钟'
            color = '#28a745'  # 绿色
        else:
            title = practice.status
            color = '#6c757d'  # 灰色
        
        events.append({
            'title': title,
            'start': practice.date.strftime('%Y-%m-%d'),
            'className': 'practice-event',
            'color': color
        })
    
    return JsonResponse(events, safe=False)

@login_required
def sheet_music(request):
    student = get_object_or_404(Student, user=request.user)
    
    # 直接从课程模块导入SheetMusic模型
    from mymanage.courses.models import SheetMusic
    
    # 获取参数
    difficulty = request.GET.get('difficulty')
    style = request.GET.get('style')
    period = request.GET.get('period')
    search = request.GET.get('search')
    
    # 获取所有曲谱（默认筛选公开的）
    sheet_music_list = SheetMusic.objects.filter(is_public=True)
    
    # 按条件筛选
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
        sheet_music_list = paginator.page(page)
    except PageNotAnInteger:
        # 如果页码不是整数，返回第一页
        sheet_music_list = paginator.page(1)
    except EmptyPage:
        # 如果页码超过了最大页数，返回最后一页
        sheet_music_list = paginator.page(paginator.num_pages)
    
    # 获取收藏的曲谱
    favorites = StudentFavorite.objects.filter(student=student).values_list('sheet_music_id', flat=True)
    
    context = {
        'student': student,
        'sheet_music_list': sheet_music_list,
        'page_obj': sheet_music_list,
        'favorites': list(favorites),
    }
    return render(request, 'students/sheet_music.html', context)

@login_required
def sheet_music_detail(request, sheet_id):
    """曲谱详情页面"""
    student = get_object_or_404(Student, user=request.user)
    
    # 使用courses.models中的SheetMusic模型
    from mymanage.courses.models import SheetMusic
    sheet = get_object_or_404(SheetMusic, id=sheet_id, is_public=True)
    
    # 检查是否收藏
    is_favorite = StudentFavorite.objects.filter(
        student=student,
        sheet_music_id=sheet.id  # 修改：使用sheet_music_id而不是sheet_music对象
    ).exists()
    
    context = {
        'student': student,
        'sheet': sheet,
        'is_favorite': is_favorite
    }
    return render(request, 'students/sheet_music_detail.html', context)

@login_required
def toggle_favorite(request, sheet_music_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        
        # 使用courses.models中的SheetMusic模型
        from mymanage.courses.models import SheetMusic
        sheet_music = get_object_or_404(SheetMusic, id=sheet_music_id)
        
        # 为了解决模型不一致的问题，使用sheet_music_id字段
        favorite, created = StudentFavorite.objects.get_or_create(
            student=student,
            sheet_music_id=sheet_music.id  # 修改：使用ID而不是对象
        )
        
        if not created:
            favorite.delete()
            is_favorite = False
        else:
            is_favorite = True
            
        return JsonResponse({
            'success': True,
            'is_favorite': is_favorite
        })
    
    return JsonResponse({'success': False}, status=400)

@login_required
def sheet_music_detail_api(request, sheet_id):
    """曲谱详情API"""
    student = get_object_or_404(Student, user=request.user)
    
    # 使用courses.models中的SheetMusic模型
    from mymanage.courses.models import SheetMusic
    sheet = get_object_or_404(SheetMusic, id=sheet_id, is_public=True)
    
    # 检查是否收藏
    is_favorite = StudentFavorite.objects.filter(
        student=student,
        sheet_music_id=sheet.id  # 修改：使用sheet_music_id而不是sheet_music对象
    ).exists()
    
    # 构建响应数据
    sheet_data = {
        'id': sheet.id,
        'title': sheet.title,
        'composer': sheet.composer,
        'difficulty': sheet.difficulty,
        'style': sheet.style,
        'period': sheet.period,
        'description': sheet.description,
        'pdf_url': sheet.file.url if sheet.file else None,
        'upload_time': sheet.upload_date.strftime('%Y-%m-%d'),
    }
    
    return JsonResponse({
        'success': True,
        'sheet': sheet_data,
        'is_favorite': is_favorite
    })

@login_required
def check_active_practice(request):
    """检查学生是否有活跃的练琴记录"""
    student = get_object_or_404(Student, user=request.user)
    current_time = timezone.now()
    today = current_time.date()
    
    try:
        # 查找是否有进行中的练琴记录
        from mymanage.courses.models import Piano
        active_practice = PracticeRecord.objects.filter(
            student=student,
            status='active',
            date=today
        ).order_by('-start_time').first()
        
        if active_practice:
            # 获取钢琴信息
            piano_number = active_practice.piano_number
            piano_brand = "未知"
            piano_model = "未知"
            
            try:
                piano = Piano.objects.get(number=piano_number)
                piano_brand = piano.brand
                piano_model = piano.model
            except Piano.DoesNotExist:
                print(f"警告：未找到编号为 {piano_number} 的钢琴")
            
            # 计算练习时间（精确到秒）
            elapsed_seconds = int((current_time - active_practice.start_time).total_seconds())
            elapsed_minutes = elapsed_seconds // 60
            remaining_seconds = elapsed_seconds % 60
            
            # 检查是否可以结束练琴
            can_end = elapsed_minutes >= 30
            
            return JsonResponse({
                'success': True,
                'has_active_practice': True,
                'practice_id': active_practice.id,
                'piano_number': piano_number,
                'piano_brand': piano_brand,
                'piano_model': piano_model,
                'elapsed_minutes': elapsed_minutes,
                'elapsed_seconds': remaining_seconds,
                'total_seconds': elapsed_seconds,
                'start_time': active_practice.start_time.isoformat(),
                'can_end': can_end,
                'message': f'检测到正在进行的练琴，已练习{elapsed_minutes}分{remaining_seconds}秒'
            })
        else:
            return JsonResponse({
                'success': True,
                'has_active_practice': False,
                'message': '没有检测到正在进行的练琴'
            })
    except Exception as e:
        import traceback
        print(f"检查活跃练琴记录时出错: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'检查活跃练琴记录时出错: {str(e)}'
        })

@login_required
def piano_practice(request):
    """专用练琴页面"""
    student = get_object_or_404(Student, user=request.user)
    practice_id = request.GET.get('practice_id')
    
    # 检查是否有活跃的练琴记录
    current_time = timezone.now()
    today = current_time.date()
    
    if not practice_id:
        # 如果没有提供practice_id，查找是否有活跃的练琴记录
        active_practice = PracticeRecord.objects.filter(
            student=student,
            status='active',
            date=today
        ).order_by('-start_time').first()
        
        if active_practice:
            practice_id = active_practice.id
        else:
            # 如果没有活跃的练琴记录，重定向到练琴主页
            messages.warning(request, '没有找到进行中的练琴记录')
            return redirect('students:practice')
    
    # 查找对应的练琴记录
    try:
        practice = PracticeRecord.objects.get(id=practice_id, student=student)
        
        # 如果练琴记录不是活跃状态，重定向到练琴主页
        if practice.status != 'active':
            messages.info(request, '该练琴记录已结束')
            return redirect('students:practice')
            
        # 获取钢琴信息
        from mymanage.courses.models import Piano
        piano_number = practice.piano_number
        piano_brand = "未知"
        piano_model = "未知"
        
        try:
            piano = Piano.objects.get(number=piano_number)
            piano_brand = piano.brand
            piano_model = piano.model
        except Piano.DoesNotExist:
            print(f"警告：未找到编号为 {piano_number} 的钢琴")
        
        context = {
            'student': student,
            'practice': practice,
            'piano_number': piano_number,
            'piano_brand': piano_brand,
            'piano_model': piano_model
        }
        
        return render(request, 'students/student_piano_practice.html', context)
        
    except PracticeRecord.DoesNotExist:
        messages.error(request, '找不到指定的练琴记录')
        return redirect('students:practice')
    except Exception as e:
        messages.error(request, f'加载练琴页面时出错: {str(e)}')
        return redirect('students:practice')

@login_required
def attendance_detail(request):
    """查看详细考勤记录，带年月日筛选功能"""
    student = get_object_or_404(Student, user=request.user)
    
    # 获取年月日筛选参数
    from datetime import datetime
    import calendar
    
    # 获取当前年份
    current_year = timezone.now().year
    
    # 生成最近15年的年份列表（当前年份往前推14年）
    years = list(range(current_year - 14, current_year + 1))
    
    # 月份选项
    months = [
        {'value': 1, 'name': '1月'},
        {'value': 2, 'name': '2月'},
        {'value': 3, 'name': '3月'},
        {'value': 4, 'name': '4月'},
        {'value': 5, 'name': '5月'},
        {'value': 6, 'name': '6月'},
        {'value': 7, 'name': '7月'},
        {'value': 8, 'name': '8月'},
        {'value': 9, 'name': '9月'},
        {'value': 10, 'name': '10月'},
        {'value': 11, 'name': '11月'},
        {'value': 12, 'name': '12月'},
        {'value': 0, 'name': '全部'}
    ]
    
    # 获取当前筛选条件
    selected_year = int(request.GET.get('year', current_year))
    selected_month = int(request.GET.get('month', timezone.now().month))
    
    # 筛选记录
    records_query = PracticeRecord.objects.filter(
        student=student
    ).filter(
        Q(status='completed') | Q(status='active')
    )
    
    # 应用年份筛选
    records_query = records_query.filter(date__year=selected_year)
    
    # 如果选择了特定月份（不是"全部"），应用月份筛选
    if selected_month > 0:
        records_query = records_query.filter(date__month=selected_month)
    
    # 按日期和开始时间倒序排序
    records = records_query.order_by('-date', '-start_time')
    
    # 分页
    paginator = Paginator(records, 20)  # 每页显示20条记录
    page = request.GET.get('page')
    records_page = paginator.get_page(page)
    
    # 计算当前筛选条件下的统计信息
    total_practice_time = records.filter(status='completed').aggregate(
        total=Sum('duration')
    )['total'] or 0
    
    avg_practice_time = records.filter(
        status='completed',
        duration__isnull=False
    ).aggregate(
        avg=Avg('duration')
    )['avg'] or 0
    
    # 计算不重复的练习天数
    distinct_days = records.values('date').distinct().count()
    
    context = {
        'student': student,
        'records': records_page,
        'years': years,
        'months': months,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'total_records': records.count(),
        'total_practice_time': round(total_practice_time / 60, 1),  # 转换为小时
        'avg_practice_time': round(avg_practice_time, 1),  # 保留一位小数
        'distinct_days': distinct_days
    }
    
    return render(request, 'students/student_attendance_detail.html', context)

@login_required
def cancel_waiting(request):
    """取消等待队列"""
    if request.method == 'POST':
        waiting_id = request.POST.get('waiting_id')
        
        if not waiting_id:
            return JsonResponse({
                'success': False,
                'message': '缺少等待记录ID'
            })
        
        try:
            from mymanage.attendance.models import WaitingQueue
            student = Student.objects.get(user=request.user)
            
            # 检查等待记录是否存在且属于当前学生
            try:
                waiting = WaitingQueue.objects.get(id=waiting_id, student=student)
            except WaitingQueue.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': '找不到对应的等待记录'
                })
            
            # 检查等待记录是否仍然激活
            if not waiting.is_active:
                return JsonResponse({
                    'success': False,
                    'message': '该等待记录已不再活跃'
                })
            
            # 取消等待
            waiting.is_active = False
            waiting.save()
            
            return JsonResponse({
                'success': True,
                'message': '成功取消等待'
            })
            
        except Exception as e:
            import traceback
            print(f"取消等待队列时出错: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'取消等待队列时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

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

from .models import Student, PracticeRecord, Attendance, StudentFavorite
from .forms import StudentProfileForm, PracticeRecordForm, AttendanceForm, SheetMusicSearchForm

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
    """处理二维码扫描请求"""
    if request.method == 'POST':
        qrcode_data = request.POST.get('qrcode_data')
        student = get_object_or_404(Student, user=request.user)
        
        if not qrcode_data:
            return JsonResponse({
                'success': False,
                'message': '二维码数据为空'
            })
        
        # 记录二维码数据以便调试
        print(f"收到二维码数据: {qrcode_data}")
        
        try:
            # 导入需要的模型
            from mymanage.attendance.models import QRCode, AttendanceRecord, AttendanceSession, WaitingQueue
            from mymanage.courses.models import Piano
            
            # 多种格式尝试匹配
            # 1. 直接尝试UUID匹配
            qrcode_obj = None
            try:
                # 去除可能存在的引号和首尾空格
                qrcode_data = qrcode_data.strip().strip('"\'')
                
                # 检查是否是UUID格式
                import uuid
                try:
                    # 尝试转换为UUID对象
                    uuid_obj = uuid.UUID(qrcode_data)
                    qrcode_obj = QRCode.objects.filter(uuid=uuid_obj).first()
                    if qrcode_obj:
                        print(f"通过UUID匹配到二维码: {qrcode_obj}")
                except ValueError:
                    # 不是有效的UUID，尝试其他方式匹配
                    pass
                
                # 如果UUID匹配失败，尝试其他方式匹配
                if not qrcode_obj:
                    # 省略其他匹配逻辑，保持原有代码...
                    pass
            
            except Exception as e:
                print(f"匹配二维码时出错: {str(e)}")
            
            # 如果找到有效的二维码
            if qrcode_obj and qrcode_obj.is_valid():
                # 获取关联的考勤会话
                session = AttendanceSession.objects.filter(qrcode=qrcode_obj).first()
                
                if not session:
                    return JsonResponse({
                        'success': False,
                        'message': '二维码未关联到有效的考勤会话'
                    })
                
                # 检查学生是否已经签到
                existing_record = AttendanceRecord.objects.filter(
                    student=student,
                    session=session,
                    status='checked_in'
                ).first()
                
                if existing_record:
                    # 如果已经签到，返回当前练琴状态
                    piano = existing_record.piano
                    elapsed_minutes = 0
                    
                    if existing_record.check_in_time:
                        elapsed_seconds = (timezone.now() - existing_record.check_in_time).total_seconds()
                        elapsed_minutes = int(elapsed_seconds / 60)
                    
                    # 检查是否有活跃的练琴记录
                    today = timezone.now().date()
                    active_practice = PracticeRecord.objects.filter(
                        student=student,
                        date=today,
                        status='active'
                    ).first()
                    
                    practice_id = active_practice.id if active_practice else None
                    
                    return JsonResponse({
                        'success': True,
                        'already_checked_in': True,
                        'message': '您已经签到，可以开始练琴',
                        'piano_number': piano.number if piano else None,
                        'piano_brand': piano.brand if piano else None,
                        'piano_model': piano.model if piano else None,
                        'elapsed_minutes': elapsed_minutes,
                        'session_id': session.id,
                        'practice_id': practice_id
                    })
                
                # 检查是否在等待队列中
                waiting_record = WaitingQueue.objects.filter(
                    session=session,
                    student=student,
                    is_active=True
                ).first()
                
                if waiting_record:
                    # 计算剩余等待时间
                    total_wait_time = waiting_record.estimated_wait_time
                    elapsed_minutes = int((timezone.now() - waiting_record.join_time).total_seconds() / 60)
                    remaining_minutes = max(0, total_wait_time - elapsed_minutes)
                    
                    return JsonResponse({
                        'success': True,
                        'waiting': True,
                        'message': f'您已在等待队列中，预计还需等待{remaining_minutes}分钟',
                        'wait_minutes': remaining_minutes,
                        'queue_position': WaitingQueue.objects.filter(
                            session=session,
                            is_active=True,
                            join_time__lt=waiting_record.join_time
                        ).count() + 1,
                        'session_id': session.id,
                        'waiting_id': waiting_record.id
                    })
                
                # 查找可用的钢琴
                available_pianos = Piano.objects.filter(
                    is_active=True,
                    is_occupied=False
                ).order_by('number')
                
                if available_pianos.exists():
                    # 有空闲钢琴，但不直接分配，返回可用钢琴信息
                    piano = available_pianos.first()
                    
                    return JsonResponse({
                        'success': True,
                        'can_start': True,
                        'message': f'扫码成功！有可用钢琴（{piano.number}号），点击开始练琴',
                        'piano_number': piano.number,
                        'piano_brand': piano.brand,
                        'piano_model': piano.model,
                        'session_id': session.id
                    })
                else:
                    # 没有空闲钢琴，计算等待时间但不直接加入队列
                    active_records = AttendanceRecord.objects.filter(
                        session=session,
                        status='checked_in'
                    ).count()
                    
                    # 假设每人平均练习30分钟，每5人增加10分钟等待时间
                    estimated_wait_time = (active_records // 5) * 10 + 5
                    
                    return JsonResponse({
                        'success': True,
                        'waiting_required': True,
                        'message': f'扫码成功！需要等待约{estimated_wait_time}分钟，点击确认加入等待',
                        'wait_minutes': estimated_wait_time,
                        'session_id': session.id
                    })
            else:
                # 二维码无效或未找到
                return JsonResponse({
                    'success': False,
                    'message': '无效的二维码或二维码已过期'
                })
                
        except Exception as e:
            import traceback
            print(f"处理二维码时出错: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'处理二维码时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def start_practice(request):
    """开始练琴函数，同时创建考勤记录"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        student = Student.objects.get(user=request.user)
        
        # 添加日志以跟踪会话ID
        print(f"收到开始练琴请求 - 学生: {student.name}, 会话ID: {session_id}")
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': '缺少会话ID'
            })
        
        try:
            from mymanage.attendance.models import AttendanceSession
            from mymanage.courses.models import Piano
            
            # 检查会话是否存在
            try:
                session = AttendanceSession.objects.get(id=session_id)
                print(f"找到会话: {session.id}, 课程: {session.course.name}")
            except AttendanceSession.DoesNotExist:
                print(f"错误: 找不到会话ID: {session_id}")
                return JsonResponse({
                    'success': False,
                    'message': '无效的会话ID'
                })
            
            # 检查学生是否有活跃的练琴记录
            active_practice = PracticeRecord.objects.filter(
                student=student,
                date=timezone.now().date(),
                status='active'
            ).first()
            
            # 如果已有活跃的练琴记录，返回该记录信息
            if active_practice:
                print(f"学生已有活跃练琴记录 ID: {active_practice.id}, 钢琴: {active_practice.piano_number}")
                # 计算已练习时间（分钟）
                current_time = timezone.now()
                elapsed_minutes = int((current_time - active_practice.start_time).total_seconds() / 60)
                
                # 获取钢琴信息
                piano_number = active_practice.piano_number
                piano_brand = "未知"
                piano_model = "未知"
                
                if piano_number:
                    try:
                        piano = Piano.objects.get(number=piano_number)
                        piano_brand = piano.brand
                        piano_model = piano.model
                    except Piano.DoesNotExist:
                        print(f"警告：练琴记录关联的钢琴 {piano_number} 不存在")
                
                # 确保考勤会话关联
                if not active_practice.attendance_session:
                    active_practice.attendance_session = session
                    active_practice.save()
                    print(f"更新练琴记录关联考勤会话: {session.id}")
                    
                return JsonResponse({
                    'success': True,
                    'message': f'继续练琴，您已在{piano_number}号钢琴练习中',
                    'practice_id': active_practice.id,
                    'elapsed_minutes': elapsed_minutes,
                    'piano_number': piano_number,
                    'piano_brand': piano_brand,
                    'piano_model': piano_model
                })
            
            # 检查钢琴是否可用
            available_pianos = Piano.objects.filter(is_occupied=False)
            if not available_pianos.exists():
                return JsonResponse({
                    'success': False,
                    'message': '当前没有可用的钢琴'
                })
            
            # 分配第一个可用钢琴
            piano = available_pianos.first()
            piano_number = piano.number
            print(f"为学生分配钢琴：{piano_number}")
            
            # 更新钢琴状态为占用
            piano.is_occupied = True
            piano.save()
            
            # 创建练琴记录（同时作为考勤记录）
            start_time = timezone.now()
            end_time = start_time + timezone.timedelta(hours=2)  # 默认2小时后结束
            
            practice = PracticeRecord.objects.create(
                student=student,
                date=start_time.date(),
                piano_number=piano_number,
                start_time=start_time,
                end_time=end_time,
                status='active',
                attendance_session=session  # 关联考勤会话
            )
            
            print(f"创建新的练琴记录: ID={practice.id}, 日期={practice.date}, 钢琴={piano_number}")
            
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
                    print(f"创建兼容性旧版考勤记录，日期={start_time.date()}")
            except Exception as e:
                print(f"创建旧版考勤记录时出错: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'message': '成功开始练琴',
                'practice_id': practice.id,
                'elapsed_minutes': 0,
                'piano_number': piano_number,
                'piano_brand': piano.brand,
                'piano_model': piano.model
            })
        
        except Exception as e:
            import traceback
            print(f"开始练琴时出错: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'开始练琴时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def check_waiting_status(request):
    """检查学生在等待队列中的状态"""
    if request.method == 'GET':
        waiting_id = request.GET.get('waiting_id')
        if not waiting_id:
            return JsonResponse({
                'success': False,
                'message': '缺少等待ID'
            })
        
        try:
            from mymanage.attendance.models import WaitingQueue, AttendanceRecord
            from mymanage.courses.models import Piano
            
            waiting = get_object_or_404(WaitingQueue, id=waiting_id)
            
            # 如果不再活跃，表示可能已被分配
            if not waiting.is_active:
                # 检查是否已经有分配的钢琴
                attendance = AttendanceRecord.objects.filter(
                    student=waiting.student,
                    session=waiting.session,
                    status='checked_in'
                ).first()
                
                if attendance and attendance.piano:
                    # 已分配钢琴
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
                        'message': '您的等待已结束，请重新扫码以分配钢琴',
                        'session_id': waiting.session.id
                    })
            
            # 计算剩余等待时间
            elapsed_minutes = int((timezone.now() - waiting.join_time).total_seconds() / 60)
            remaining_minutes = max(0, waiting.estimated_wait_time - elapsed_minutes)
            
            # 获取当前队列位置
            queue_position = WaitingQueue.objects.filter(
                session=waiting.session,
                is_active=True,
                join_time__lt=waiting.join_time
            ).count() + 1
            
            # 检查是否有空闲钢琴
            available_pianos = Piano.objects.filter(
                is_active=True,
                is_occupied=False
            ).exists()
            
            if available_pianos and queue_position <= 1:
                # 更新等待状态为非活跃
                waiting.is_active = False
                waiting.save()
                
                # 获取第一个可用钢琴
                piano = Piano.objects.filter(
                    is_active=True,
                    is_occupied=False
                ).first()
                
                # 更新考勤记录，分配钢琴
                attendance = AttendanceRecord.objects.filter(
                    student=waiting.student,
                    session=waiting.session
                ).first()
                
                if attendance:
                    attendance.piano = piano
                    attendance.save()
                    
                    # 将钢琴标记为已占用
                    piano.is_occupied = True
                    piano.save()
                
                return JsonResponse({
                    'success': True,
                    'ready': True,
                    'message': f'您可以开始练琴，已为您分配{piano.number}号钢琴',
                    'piano_number': piano.number,
                    'piano_brand': piano.brand,
                    'piano_model': piano.model,
                    'session_id': waiting.session.id
                })
            else:
                # 更新预计等待时间
                active_records = AttendanceRecord.objects.filter(
                    session=waiting.session,
                    status='checked_in',
                    piano__isnull=False
                ).count()
                
                waiting_count = WaitingQueue.objects.filter(
                    session=waiting.session,
                    is_active=True,
                    join_time__lt=waiting.join_time
                ).count()
                
                # 重新计算等待时间
                new_estimated_wait = ((active_records + waiting_count) // 5) * 10 + 5
                
                # 如果新估计比剩余时间更长，则更新
                if new_estimated_wait > remaining_minutes:
                    waiting.estimated_wait_time = elapsed_minutes + new_estimated_wait
                    waiting.save()
                    remaining_minutes = new_estimated_wait
                
                return JsonResponse({
                    'success': True,
                    'ready': False,
                    'message': f'您当前排在第{queue_position}位，预计还需等待{remaining_minutes}分钟',
                    'queue_position': queue_position,
                    'wait_minutes': remaining_minutes,
                    'session_id': waiting.session.id
                })
                
        except Exception as e:
            import traceback
            print(f"检查等待状态时出错: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'检查等待状态时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def join_waiting_queue(request):
    """将学生加入等待队列"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        student = get_object_or_404(Student, user=request.user)
        
        try:
            from mymanage.attendance.models import AttendanceSession, WaitingQueue, AttendanceRecord
            
            session = get_object_or_404(AttendanceSession, id=session_id)
            
            # 检查是否已经在等待队列中
            existing_wait = WaitingQueue.objects.filter(
                session=session,
                student=student,
                is_active=True
            ).first()
            
            if existing_wait:
                # 如果已经在队列中，返回当前等待状态
                elapsed_minutes = int((timezone.now() - existing_wait.join_time).total_seconds() / 60)
                remaining_minutes = max(0, existing_wait.estimated_wait_time - elapsed_minutes)
                
                return JsonResponse({
                    'success': True,
                    'message': f'您已在等待队列中，预计还需等待{remaining_minutes}分钟',
                    'wait_minutes': remaining_minutes,
                    'queue_position': WaitingQueue.objects.filter(
                        session=session,
                        is_active=True,
                        join_time__lt=existing_wait.join_time
                    ).count() + 1,
                    'waiting_id': existing_wait.id
                })
            
            # 检查是否已经签到
            existing_record = AttendanceRecord.objects.filter(
                student=student,
                session=session,
                status='checked_in'
            ).first()
            
            if existing_record and existing_record.piano and existing_record.piano.is_occupied:
                # 如果已经签到并分配了钢琴，不需要等待
                return JsonResponse({
                    'success': False,
                    'message': '您已经签到并分配了钢琴，无需等待'
                })
            
            # 计算预计等待时间
            active_records = AttendanceRecord.objects.filter(
                session=session,
                status='checked_in'
            ).count()
            
            waiting_count = WaitingQueue.objects.filter(
                session=session,
                is_active=True
            ).count()
            
            # 估算等待时间：每5人增加10分钟，基础等待5分钟
            estimated_wait_time = ((active_records + waiting_count) // 5) * 10 + 5
            
            # 创建等待记录
            waiting_record = WaitingQueue.objects.create(
                student=student,
                session=session,
                join_time=timezone.now(),
                estimated_wait_time=estimated_wait_time,
                is_active=True
            )
            
            # 如果还没有创建考勤记录，则创建一个但不分配钢琴
            if not existing_record:
                AttendanceRecord.objects.create(
                    student=student,
                    session=session,
                    status='checked_in',
                    check_in_time=timezone.now()
                )
            
            queue_position = WaitingQueue.objects.filter(
                session=session,
                is_active=True,
                join_time__lt=waiting_record.join_time
            ).count() + 1
            
            return JsonResponse({
                'success': True,
                'message': f'成功加入等待队列，您当前排在第{queue_position}位，预计等待{estimated_wait_time}分钟',
                'wait_minutes': estimated_wait_time,
                'queue_position': queue_position,
                'waiting_id': waiting_record.id
            })
            
        except Exception as e:
            import traceback
            print(f"加入等待队列时出错: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'加入等待队列时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def end_practice(request):
    """结束练琴（签退），同时更新考勤记录"""
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        practice_id = request.POST.get('practice_id')
        qrcode_data = request.POST.get('qrcode_data')
        
        print(f"结束练琴请求: 学生={student.name}, 练琴ID={practice_id}, 二维码数据={qrcode_data}")
        
        if not practice_id:
            return JsonResponse({
                'success': False,
                'message': '缺少练琴记录ID'
            })
        
        try:
            # 获取练琴记录
            practice = get_object_or_404(PracticeRecord, id=practice_id, student=student)
            print(f"找到练琴记录: 开始时间={practice.start_time}, 状态={practice.status}")
            
            # 如果记录状态不是active，则返回错误
            if practice.status != 'active':
                return JsonResponse({
                    'success': False,
                    'message': '没有找到进行中的练琴记录'
                })
            
            # 检查是否满足最低练习时间（30分钟）
            now = timezone.now()
            practice_duration_seconds = (now - practice.start_time).total_seconds()
            practice_duration = practice_duration_seconds / 60  # 分钟
            
            minutes = int(practice_duration)
            seconds = int((practice_duration - minutes) * 60)
            
            print(f"计算练琴时长: {minutes}分{seconds}秒 (共{practice_duration:.2f}分钟)")
            
            if practice_duration < 30:
                remaining_minutes = int(30 - practice_duration)
                remaining_seconds = int(((30 - practice_duration) % 1) * 60)
                
                return JsonResponse({
                    'success': False,
                    'message': f'练琴时间不足30分钟，当前已练习{minutes}分{seconds}秒，还需继续练习{remaining_minutes}分{remaining_seconds}秒',
                    'remaining_minutes': remaining_minutes,
                    'remaining_seconds': remaining_seconds,
                    'elapsed_minutes': minutes,
                    'elapsed_seconds': seconds,
                    'total_seconds': int(practice_duration_seconds)
                })
            
            # 释放钢琴
            from mymanage.courses.models import Piano
            piano = None
            try:
                piano = Piano.objects.get(number=practice.piano_number)
                piano.is_occupied = False
                piano.save()
                print(f"释放钢琴: 编号={piano.number}")
            except Piano.DoesNotExist:
                print(f"警告: 无法找到编号为 {practice.piano_number} 的钢琴")
            
            # 更新练琴记录
            practice.end_time = now
            practice.duration = practice_duration
            practice.status = 'completed'
            practice.save()
            print(f"更新练琴记录完成: 结束时间={practice.end_time}, 时长={practice.duration:.2f}分钟")
            
            # 更新旧版Attendance考勤记录（仅为兼容）
            try:
                # 获取旧版考勤记录
                practice_date = practice.start_time.date()
                attendance = Attendance.objects.filter(
                    student=student,
                    date=practice_date
                ).first()
                
                if attendance:
                    # 更新签退时间
                    attendance.check_out_time = now
                    attendance.save()
                    print(f"更新旧版考勤记录: 日期={practice_date}, 签退时间={now}")
                else:
                    # 如果没有记录，创建一个完整记录
                    Attendance.objects.create(
                        student=student,
                        date=practice_date,
                        check_in_time=practice.start_time,
                        check_out_time=now,
                        status='present'
                    )
                    print(f"创建完整旧版考勤记录: 日期={practice_date}")
            except Exception as e:
                print(f"更新旧版考勤记录时出错: {str(e)}")
                traceback.print_exc()
            
            return JsonResponse({
                'success': True,
                'message': f'练琴结束，本次练习时长：{minutes}分{seconds}秒',
                'duration_minutes': minutes,
                'duration_seconds': seconds,
                'total_seconds': int(practice_duration_seconds),
                'practice_record_id': practice.id
            })
                
        except Exception as e:
            import traceback
            print(f"结束练琴时出错: {str(e)}")
            print(traceback.format_exc())
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

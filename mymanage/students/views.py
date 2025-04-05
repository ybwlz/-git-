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
                    
                    return JsonResponse({
                        'success': True,
                        'already_checked_in': True,
                        'message': '您已经签到，可以开始练琴',
                        'piano_number': piano.number if piano else None,
                        'piano_brand': piano.brand if piano else None,
                        'piano_model': piano.model if piano else None,
                        'elapsed_minutes': elapsed_minutes,
                        'session_id': session.id
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
    """开始练琴（扫码确认后）"""
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        session_id = request.POST.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': '缺少会话ID'
            })
        
        try:
            from mymanage.attendance.models import AttendanceSession, AttendanceRecord
            from mymanage.courses.models import Piano
            
            # 获取会话
            session = get_object_or_404(AttendanceSession, id=session_id)
            
            # 检查学生是否已经签到
            existing_record = AttendanceRecord.objects.filter(
                student=student,
                session=session
            ).first()
            
            if existing_record:
                return JsonResponse({
                    'success': False,
                    'message': '您已经签到过此课程'
                })
            
            # 查找可用的钢琴
            available_pianos = Piano.objects.filter(
                is_active=True,
                is_occupied=False
            ).order_by('number')
            
            if available_pianos.exists():
                # 有空闲钢琴
                piano = available_pianos.first()
                piano.is_occupied = True
                piano.save()
                
                # 创建考勤记录
                attendance = AttendanceRecord.objects.create(
                    session=session,
                    student=student,
                    piano=piano,
                    status='checked_in',
                    check_in_method='qrcode'
                )
                
                # 创建练琴记录
                today = timezone.now().date()
                practice = PracticeRecord.objects.create(
                    student=student,
                    date=today,
                    start_time=timezone.now(),
                    piano_number=piano.number,
                    status='active'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'练琴开始！已分配{piano.number}号钢琴',
                    'piano_number': piano.number,
                    'practice_id': practice.id,
                    'attendance_id': attendance.id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '没有可用的钢琴，请稍后再试'
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
def join_waiting_queue(request):
    """加入等待队列"""
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        session_id = request.POST.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': '缺少会话ID'
            })
        
        try:
            from mymanage.attendance.models import AttendanceSession, WaitingQueue, AttendanceRecord
            
            # 获取会话
            session = get_object_or_404(AttendanceSession, id=session_id)
            
            # 检查学生是否已经签到
            if AttendanceRecord.objects.filter(student=student, session=session).exists():
                return JsonResponse({
                    'success': False,
                    'message': '您已经签到过此课程'
                })
            
            # 检查是否已在等待队列中
            existing_waiting = WaitingQueue.objects.filter(
                student=student,
                session=session,
                is_active=True
            ).first()
            
            if existing_waiting:
                # 已在队列中，返回位置信息
                queue_position = WaitingQueue.objects.filter(
                    session=session,
                    is_active=True,
                    join_time__lt=existing_waiting.join_time
                ).count() + 1
                
                return JsonResponse({
                    'success': True,
                    'already_waiting': True,
                    'message': f'您已在等待队列中，当前排在第{queue_position}位',
                    'queue_position': queue_position,
                    'wait_minutes': existing_waiting.estimated_wait_time,
                    'waiting_id': existing_waiting.id
                })
            
            # 计算预计等待时间
            active_records = AttendanceRecord.objects.filter(
                session=session,
                status='checked_in'
            ).count()
            
            # 假设每人平均练习30分钟，每5人增加10分钟等待时间
            estimated_wait_time = (active_records // 5) * 10 + 5
            
            # 创建等待记录
            waiting = WaitingQueue.objects.create(
                session=session,
                student=student,
                estimated_wait_time=estimated_wait_time
            )
            
            # 获取队列位置
            queue_position = WaitingQueue.objects.filter(
                session=session,
                is_active=True,
                join_time__lt=waiting.join_time
            ).count() + 1
            
            return JsonResponse({
                'success': True,
                'message': f'已成功加入等待队列，当前排在第{queue_position}位',
                'queue_position': queue_position,
                'wait_minutes': estimated_wait_time,
                'waiting_id': waiting.id
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
    """结束练琴（签退）"""
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        practice_id = request.POST.get('practice_id')
        
        if not practice_id:
            return JsonResponse({
                'success': False,
                'message': '缺少练琴记录ID'
            })
        
        try:
            # 获取练琴记录
            practice = get_object_or_404(PracticeRecord, id=practice_id, student=student)
            
            # 如果记录状态不是active，则返回错误
            if practice.status != 'active':
                return JsonResponse({
                    'success': False,
                    'message': '没有找到进行中的练琴记录'
                })
            
            # 检查是否满足最低练习时间（30分钟）
            now = timezone.now()
            practice_duration = (now - practice.start_time).total_seconds() / 60  # 分钟
            
            if practice_duration < 30:
                return JsonResponse({
                    'success': False,
                    'message': f'练琴时间不足30分钟，当前已练习{int(practice_duration)}分钟',
                    'remaining_minutes': int(30 - practice_duration)
                })
            
            # 更新练琴记录
            practice.end_time = now
            practice.duration = practice_duration
            practice.status = 'completed'
            practice.save()
            
            # 释放钢琴
            from mymanage.courses.models import Piano
            try:
                piano = Piano.objects.get(number=practice.piano_number)
                piano.is_occupied = False
                piano.save()
            except Piano.DoesNotExist:
                print(f"警告: 无法找到编号为 {practice.piano_number} 的钢琴")
            
            # 更新考勤记录
            from mymanage.attendance.models import AttendanceRecord
            attendance_records = AttendanceRecord.objects.filter(
                student=student,
                piano__number=practice.piano_number,
                status='checked_in'
            )
            
            for record in attendance_records:
                record.status = 'checked_out'
                record.check_out_time = now
                record.duration = (record.check_out_time - record.check_in_time).total_seconds() / 3600  # 小时
                record.duration_minutes = record.duration * 60  # 分钟
                record.save()
            
            return JsonResponse({
                'success': True,
                'message': f'练琴结束，本次练习时长：{int(practice_duration)}分钟',
                'duration': int(practice_duration)
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
    """检查当前练琴状态"""
    student = get_object_or_404(Student, user=request.user)
    today = timezone.now().date()
    current_time = timezone.now()
    
    # 获取今日练琴记录 - 添加条件确保end_time大于当前时间或者为空
    active_practice = PracticeRecord.objects.filter(
        student=student,
        date=today,
        status='active',
        end_time__gt=current_time  # 确保只返回真正活跃的记录
    ).first()
    
    # 如果没有找到符合条件的记录，但有状态为active的记录，自动将其状态更新为completed
    if not active_practice:
        expired_practices = PracticeRecord.objects.filter(
            student=student,
            date=today,
            status='active'
        )
        for practice in expired_practices:
            practice.status = 'completed'
            practice.save()
    
    completed_practice = PracticeRecord.objects.filter(
        student=student,
        date=today,
        status='completed'
    ).first()
    
    # 检查是否在等待队列中
    from mymanage.attendance.models import WaitingQueue
    waiting = WaitingQueue.objects.filter(
        student=student,
        is_active=True
    ).first()
    
    if active_practice:
        # 计算已练习时间
        elapsed_seconds = (timezone.now() - active_practice.start_time).total_seconds()
        elapsed_minutes = int(elapsed_seconds / 60)
        
        # 检查是否已满30分钟
        can_checkout = elapsed_minutes >= 30
        
        return JsonResponse({
            'status': 'active',
            'practice_id': active_practice.id,
            'start_time': active_practice.start_time.strftime('%H:%M'),
            'elapsed_minutes': elapsed_minutes,
            'can_checkout': can_checkout,
            'remaining_minutes': max(0, 30 - elapsed_minutes) if not can_checkout else 0,
            'piano_number': active_practice.piano_number
        })
    elif waiting:
        # 计算等待时间
        queue_position = WaitingQueue.objects.filter(
            session=waiting.session,
            is_active=True,
            join_time__lt=waiting.join_time
        ).count() + 1
        
        # 计算剩余等待时间
        total_wait_minutes = waiting.estimated_wait_time
        elapsed_wait_minutes = int((timezone.now() - waiting.join_time).total_seconds() / 60)
        remaining_minutes = max(0, total_wait_minutes - elapsed_wait_minutes)
        
        return JsonResponse({
            'status': 'waiting',
            'waiting_id': waiting.id,
            'join_time': waiting.join_time.strftime('%H:%M'),
            'position': queue_position,
            'wait_minutes': remaining_minutes
        })
    elif completed_practice:
        return JsonResponse({
            'status': 'completed',
            'practice_id': completed_practice.id,
            'start_time': completed_practice.start_time.strftime('%H:%M') if completed_practice.start_time else None,
            'end_time': completed_practice.end_time.strftime('%H:%M') if completed_practice.end_time else None,
            'duration': int(completed_practice.duration) if completed_practice.duration else 0
        })
    else:
        return JsonResponse({
            'status': 'inactive'
        })

@login_required
def attendance(request):
    student = get_object_or_404(Student, user=request.user)
    today = timezone.now().date()
    
    # 从考勤应用获取考勤记录，而不是使用学生应用的Attendance模型
    from mymanage.attendance.models import AttendanceRecord
    
    # 获取今日考勤记录
    today_attendance = AttendanceRecord.objects.filter(
        student=student,
        check_in_time__date=today
    ).first()
    
    # 获取历史考勤记录
    attendances = AttendanceRecord.objects.filter(student=student).order_by('-check_in_time')
    paginator = Paginator(attendances, 10)
    page = request.GET.get('page')
    attendances_page = paginator.get_page(page)
    
    # 获取考勤统计数据
    total_days = AttendanceRecord.objects.filter(student=student).count()
    present_days = AttendanceRecord.objects.filter(student=student, status='checked_out').count()
    
    # 如果有历史记录，计算出勤率
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    # 获取本月考勤
    current_month = timezone.now().month
    current_year = timezone.now().year
    month_attendances = AttendanceRecord.objects.filter(
        student=student,
        check_in_time__month=current_month,
        check_in_time__year=current_year
    ).count()
    
    context = {
        'student': student,
        'today_attendance': today_attendance,
        'attendances': attendances_page,
        'total_days': total_days,
        'present_days': present_days,
        'attendance_rate': attendance_rate,
        'month_attendances': month_attendances
    }
    return render(request, 'students/student_attendance.html', context)

@login_required
def attendance_history(request):
    """获取考勤历史数据"""
    student = get_object_or_404(Student, user=request.user)
    
    # 从考勤应用获取考勤记录
    from mymanage.attendance.models import AttendanceRecord
    
    # 获取所有考勤记录
    attendances = AttendanceRecord.objects.filter(student=student).order_by('-check_in_time')
    
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
    
    # 从考勤应用获取考勤记录
    from mymanage.attendance.models import AttendanceRecord
    
    # 获取月度考勤统计
    now = timezone.now()
    months = []
    for i in range(6):
        month = now.month - i if now.month - i > 0 else now.month - i + 12
        year = now.year if now.month - i > 0 else now.year - 1
        
        month_count = AttendanceRecord.objects.filter(
            student=student,
            check_in_time__month=month,
            check_in_time__year=year
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
        
        week_count = AttendanceRecord.objects.filter(
            student=student,
            check_in_time__date__gte=start_date,
            check_in_time__date__lte=end_date
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
    
    # 查询该月的所有考勤记录
    attendances = Attendance.objects.filter(
        student=student,
        date__year=year,
        date__month=month
    )
    
    # 格式化为日历事件
    events = []
    for attendance in attendances:
        color = '#4CAF50' if attendance.status == 'present' else '#F44336'
        
        events.append({
            'title': '已签到' if attendance.status == 'present' else '缺勤',
            'start': attendance.date.strftime('%Y-%m-%d'),
            'className': attendance.status,
            'color': color
        })
    
    # 添加练琴记录
    practices = PracticeRecord.objects.filter(
        student=student,
        date__year=year,
        date__month=month
    )
    
    for practice in practices:
        events.append({
            'title': f'练琴 {practice.duration} 分钟',
            'start': practice.date.strftime('%Y-%m-%d'),
            'className': 'practice-event',
            'color': '#6c5ce7'
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

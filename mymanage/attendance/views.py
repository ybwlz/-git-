from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
import datetime
import json
import uuid as uuid_lib

from .models import QRCode, AttendanceSession, AttendanceRecord, WaitingQueue
from mymanage.courses.models import Course, CourseSchedule, Piano
from mymanage.students.models import Student
from mymanage.users.decorators import teacher_required


@login_required
def attendance_dashboard(request):
    """考勤仪表板（根据用户角色显示不同内容）"""
    if hasattr(request.user, 'teacher_profile'):
        # 教师仪表板
        active_sessions = AttendanceSession.objects.filter(
            status='active', 
            created_by=request.user
        ).order_by('-start_time')
        
        records_today = AttendanceRecord.objects.filter(
            session__created_by=request.user,
            check_in_time__date=timezone.now().date()
        ).count()
        
        context = {
            'active_sessions': active_sessions,
            'records_today': records_today,
            'user_type': 'teacher'
        }
    elif hasattr(request.user, 'student_profile'):
        # 学生仪表板
        student = request.user.student_profile
        
        active_record = AttendanceRecord.objects.filter(
            student=student,
            status='checked_in'
        ).first()
        
        waiting = WaitingQueue.objects.filter(
            student=student,
            is_active=True
        ).first()
        
        recent_records = AttendanceRecord.objects.filter(
            student=student
        ).order_by('-check_in_time')[:5]
        
        context = {
            'active_record': active_record,
            'waiting': waiting,
            'recent_records': recent_records,
            'user_type': 'student'
        }
    else:
        # 管理员或其他
        active_sessions = AttendanceSession.objects.filter(status='active').order_by('-start_time')
        records_today = AttendanceRecord.objects.filter(
            check_in_time__date=timezone.now().date()
        ).count()
        
        context = {
            'active_sessions': active_sessions,
            'records_today': records_today,
            'user_type': 'admin'
        }
    
    return render(request, 'attendance/dashboard.html', context)


@teacher_required
def create_session(request):
    """创建考勤会话"""
    if request.method == 'POST':
        course_id = request.POST.get('course')
        schedule_id = request.POST.get('schedule')
        
        # 检查是否已存在活跃会话
        existing_session = AttendanceSession.objects.filter(
            course_id=course_id,
            status='active'
        ).first()
        
        if existing_session:
            messages.warning(request, f'课程 {existing_session.course.name} 已有活跃的考勤会话')
            return redirect('attendance_session_detail', session_id=existing_session.id)
        
        # 创建QR码
        course = get_object_or_404(Course, id=course_id)
        schedule = get_object_or_404(CourseSchedule, id=schedule_id)
        
        # 设置二维码过期时间（6小时）
        expires_at = timezone.now() + datetime.timedelta(hours=6)
        
        qrcode = QRCode.objects.create(
            course=course,
            expires_at=expires_at
        )
        
        # 创建考勤会话
        session = AttendanceSession.objects.create(
            course=course,
            schedule=schedule,
            qrcode=qrcode,
            created_by=request.user,
            status='active'
        )
        
        messages.success(request, f'已成功创建 {course.name} 的考勤会话')
        return redirect('attendance_session_detail', session_id=session.id)
    
    # GET请求，显示创建表单
    courses = Course.objects.filter(teacher__user=request.user)
    schedules = CourseSchedule.objects.filter(course__teacher__user=request.user)
    
    context = {
        'courses': courses,
        'schedules': schedules
    }
    
    return render(request, 'attendance/create_session.html', context)


@login_required
def session_detail(request, session_id):
    """考勤会话详情"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # 检查权限（只有相关教师和管理员可以查看）
    if not (request.user.is_superuser or request.user.is_admin_user or 
            (hasattr(request.user, 'teacher_profile') and session.created_by == request.user)):
        messages.error(request, '您没有权限查看此考勤会话')
        return redirect('attendance_dashboard')
    
    records = AttendanceRecord.objects.filter(session=session).order_by('-check_in_time')
    waiting_queue = WaitingQueue.objects.filter(session=session, is_active=True).order_by('join_time')
    
    context = {
        'session': session,
        'records': records,
        'waiting_queue': waiting_queue,
        'qrcode_url': session.qrcode.qr_code_image.url if session.qrcode and session.qrcode.qr_code_image else None
    }
    
    return render(request, 'attendance/session_detail.html', context)


@teacher_required
def close_session(request, session_id):
    """关闭考勤会话"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # 只有创建者可以关闭会话
    if session.created_by != request.user and not request.user.is_superuser:
        messages.error(request, '您没有权限关闭此考勤会话')
        return redirect('attendance_session_detail', session_id=session.id)
    
    if request.method == 'POST':
        session.close_session()
        messages.success(request, f'已成功关闭 {session.course.name} 的考勤会话')
        return redirect('attendance_dashboard')
    
    return render(request, 'attendance/close_session_confirm.html', {'session': session})


@login_required
def scan_qrcode(request):
    """扫描二维码"""
    if request.method == 'POST' and hasattr(request.user, 'student_profile'):
        try:
            data = json.loads(request.body)
            qrcode_uuid = data.get('qrcode_uuid')
            
            # 查找二维码
            qrcode = get_object_or_404(QRCode, uuid=qrcode_uuid)
            
            # 检查二维码是否有效
            if not qrcode.is_valid():
                return JsonResponse({
                    'success': False,
                    'message': '二维码已过期'
                })
            
            # 检查是否有活跃会话
            session = AttendanceSession.objects.filter(qrcode=qrcode, status='active').first()
            if not session:
                return JsonResponse({
                    'success': False,
                    'message': '找不到活跃的考勤会话'
                })
            
            student = request.user.student_profile
            
            # 检查学生是否已在队列中或已签到
            if AttendanceRecord.objects.filter(student=student, session=session, status='checked_in').exists():
                return JsonResponse({
                    'success': False,
                    'message': '您已经签到并正在练习'
                })
            
            if WaitingQueue.objects.filter(student=student, session=session, is_active=True).exists():
                return JsonResponse({
                    'success': False,
                    'message': '您已在等待队列中'
                })
            
            # 检查是否有可用钢琴
            available_piano = Piano.objects.filter(is_active=True, is_occupied=False).order_by('number').first()
            
            if available_piano:
                # 有可用钢琴，直接签到
                available_piano.is_occupied = True
                available_piano.save()
                
                # 使用当前时间创建考勤记录
                current_time = timezone.now()
                print(f"DEBUG - 创建考勤记录时间: {current_time}, 日期: {current_time.date()}")
                record = AttendanceRecord.objects.create(
                    session=session,
                    student=student,
                    piano=available_piano,
                    status='checked_in',
                    check_in_time=current_time  # 明确设置签到时间为当前时间
                )
                print(f"DEBUG - 创建的考勤记录ID: {record.id}, 时间: {record.check_in_time}, 日期: {record.check_in_time.date()}")
                
                return JsonResponse({
                    'success': True, 
                    'status': 'assigned',
                    'message': f'已为您分配钢琴 {available_piano.number} 号',
                    'piano': available_piano.number
                })
            else:
                # 没有可用钢琴，加入等待队列
                waiting_queue_count = WaitingQueue.objects.filter(
                    session=session,
                    is_active=True
                ).count()
                
                # 计算预计等待时间（每人30分钟）
                wait_time = waiting_queue_count * 30
                
                WaitingQueue.objects.create(
                    session=session,
                    student=student,
                    estimated_wait_time=wait_time
                )
                
                return JsonResponse({
                    'success': True,
                    'status': 'waiting',
                    'message': f'您已加入等待队列，当前排队位置：{waiting_queue_count + 1}，预计等待时间：{wait_time}分钟',
                    'position': waiting_queue_count + 1,
                    'estimated_wait_time': wait_time
                })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'错误：{str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '无效的请求'})


@login_required
def student_attendance_history(request):
    """学生考勤历史"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, '只有学生可以查看自己的考勤历史')
        return redirect('index')
    
    student = request.user.student_profile
    
    # 获取过滤参数
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    records = AttendanceRecord.objects.filter(student=student)
    
    if month and year:
        records = records.filter(
            check_in_time__month=month,
            check_in_time__year=year
        )
    
    # 按日期分组
    attendance_by_date = {}
    for record in records:
        date = record.check_in_time.date()
        if date not in attendance_by_date:
            attendance_by_date[date] = []
        attendance_by_date[date].append(record)
    
    context = {
        'attendance_by_date': attendance_by_date,
        'student': student
    }
    
    return render(request, 'attendance/student_history.html', context)


@teacher_required
def teacher_attendance_stats(request):
    """教师考勤统计"""
    teacher = request.user.teacher_profile
    
    # 获取过滤参数
    month = request.GET.get('month')
    year = request.GET.get('year')
    course_id = request.GET.get('course')
    
    # 查询相关课程
    courses = Course.objects.filter(teacher=teacher)
    
    # 创建查询条件
    query_params = {'session__course__teacher': teacher}
    
    if month and year:
        query_params['check_in_time__month'] = month
        query_params['check_in_time__year'] = year
    
    if course_id:
        query_params['session__course_id'] = course_id
    
    # 查询考勤记录
    records = AttendanceRecord.objects.filter(**query_params)
    
    # 统计数据
    total_records = records.count()
    total_duration = sum((r.duration.total_seconds() if r.duration else 0) for r in records)
    total_duration_hours = total_duration / 3600
    
    # 按学生分组
    records_by_student = {}
    for record in records:
        if record.student_id not in records_by_student:
            records_by_student[record.student_id] = {
                'student': record.student,
                'count': 0,
                'total_duration': 0
            }
        
        records_by_student[record.student_id]['count'] += 1
        records_by_student[record.student_id]['total_duration'] += record.duration.total_seconds() if record.duration else 0
    
    # 计算每个学生的总时长（小时）
    for student_id in records_by_student:
        records_by_student[student_id]['total_duration_hours'] = records_by_student[student_id]['total_duration'] / 3600
    
    context = {
        'courses': courses,
        'selected_course_id': course_id,
        'total_records': total_records,
        'total_duration_hours': total_duration_hours,
        'records_by_student': records_by_student.values()
    }
    
    return render(request, 'attendance/teacher_stats.html', context)


@login_required
@teacher_required
def generate_qrcode(request):
    """生成新的二维码"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            course_id = data.get('course_id')
            hours = int(data.get('hours', 2))
            
            # 获取课程
            teacher = request.user.teacher_profile
            course = None
            
            # 先结束该教师的所有活跃会话
            current_time = timezone.now()
            active_sessions = AttendanceSession.objects.filter(
                created_by=request.user,
                status='active'
            )
            for session in active_sessions:
                session.status = 'closed'
                session.is_active = False
                session.end_time = current_time
                session.save()
                
            try:
                # 尝试获取指定的课程
                if course_id:
                    course = Course.objects.get(id=course_id, teacher=teacher)
            except Course.DoesNotExist:
                # 如果未找到课程，使用默认课程
                course = None
            
            # 如果没有找到课程或没有提供课程ID，则创建一个默认课程
            if not course:
                # 先获取或创建一个有效的钢琴级别
                from mymanage.courses.models import PianoLevel
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
            
            # 设置二维码过期时间
            expires_at = current_time + datetime.timedelta(hours=hours)
            
            # 创建二维码
            qrcode_uuid = str(uuid_lib.uuid4())
            qrcode = QRCode.objects.create(
                course=course,
                uuid=uuid_lib.UUID(qrcode_uuid),
                code=qrcode_uuid,
                expires_at=expires_at
            )
            
            # 获取当前weekday
            weekday = current_time.weekday()
            
            # 获取或创建课程时间表
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
                qrcode=qrcode,
                created_by=request.user,
                start_time=current_time,
                end_time=expires_at,
                description=f"手动生成的考勤 - {current_time.strftime('%Y-%m-%d %H:%M')}",
                status='active'
            )
            
            # 构建二维码图片的URL
            qrcode_url = request.build_absolute_uri(qrcode.qr_code_image.url) if qrcode.qr_code_image else None
            
            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'qrcode_uuid': qrcode_uuid,
                'qrcode_url': qrcode_url,
                'course_name': course.name,
                'expires_at': expires_at.isoformat(),
                'message': '二维码生成成功'
            })
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            return JsonResponse({
                'success': False,
                'message': f'生成二维码时出错: {str(e)}',
                'traceback': error_traceback
            })
    
    return JsonResponse({
        'success': False,
        'message': '仅支持POST请求'
    })


@teacher_required
def end_session(request):
    """结束考勤会话"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            
            # 获取会话
            session = get_object_or_404(AttendanceSession, id=session_id)
            
            # 验证权限
            if session.created_by != request.user and not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'message': '您没有权限结束此考勤会话'
                }, status=403)
            
            # 关闭会话
            session.status = 'closed'
            session.is_active = False
            
            # 确保会话有结束时间
            if not session.end_time:
                session.end_time = timezone.now()
                
            session.save()
            
            return JsonResponse({
                'success': True,
                'message': '考勤会话已结束'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'发生错误: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': '仅支持POST请求'
    }, status=405)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json
import qrcode
from io import BytesIO
import base64
from django.db.models import Sum, Count, Avg, Q

from .models import Student, PracticeRecord, Attendance, SheetMusic, StudentFavorite
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
    
    # 获取考勤统计
    total_attendance = Attendance.objects.filter(
        student=student
    ).count()
    
    # 获取本月数据
    current_month = timezone.now().month
    this_month_practice = PracticeRecord.objects.filter(
        student=student,
        date__month=current_month
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    context = {
        'form': form,
        'student': student,
        'practice_records': student.practice_records.all()[:5],
        'attendances': student.attendances.all()[:5],
        'total_practice_time': total_practice_time,
        'total_attendance': total_attendance,
        'this_month_practice': this_month_practice
    }
    return render(request, 'students/student_profile.html', context)

@login_required
def update_profile(request):
    student = get_object_or_404(Student, user=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, '个人信息更新成功！')
            return redirect('students:profile')
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
    
    # 获取今日练琴记录
    today_practice = PracticeRecord.objects.filter(
        student=student,
        date=today
    ).first()
    
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
    
    # 定义钢琴品牌和型号的映射（可以从数据库获取）
    piano_brands = {
        1: "雅马哈 (Yamaha)",
        2: "卡瓦依 (Kawai)",
        3: "施坦威 (Steinway)",
        4: "珠江 (Pearl River)",
        5: "雅马哈 (Yamaha)",
        6: "卡瓦依 (Kawai)",
        7: "施坦威 (Steinway)"
    }
    
    piano_models = {
        1: "YDP-164",
        2: "CA48",
        3: "S-155",
        4: "EU120",
        5: "YDP-144",
        6: "CN29",
        7: "K-132"
    }
    
    # 获取钢琴信息
    piano_brand = None
    piano_model = None
    if today_practice and today_practice.piano_number:
        piano_number = today_practice.piano_number
        piano_brand = piano_brands.get(piano_number, "未知品牌")
        piano_model = piano_models.get(piano_number, "未知型号")
    
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
        
        # 自动安排练琴时间
        active_practices = PracticeRecord.objects.filter(
            date=today,
            end_time__gt=timezone.now()
        )
        
        # 获取所有已分配的钢琴编号
        used_pianos = active_practices.values_list('piano_number', flat=True)
        
        if active_practices.count() < 7:
            # 有空闲钢琴，找到一个未被使用的钢琴编号
            available_piano = next(i for i in range(1, 8) if i not in used_pianos)
            
            # 创建练琴记录
            next_practice = PracticeRecord.objects.create(
                student=student,
                date=today,
                start_time=timezone.now(),
                end_time=timezone.now() + timedelta(minutes=30),
                duration=30,
                piano_number=available_piano
            )
            
            return JsonResponse({
                'success': True,
                'message': '签到成功，已分配钢琴',
                'practice_time': next_practice.start_time.strftime('%H:%M'),
                'piano_number': next_practice.piano_number,
                'waiting': False
            })
        else:
            # 所有钢琴都在使用中，安排等待
            # 找出最早结束的练琴记录
            earliest_end = active_practices.order_by('end_time').first()
            
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
            
            return JsonResponse({
                'success': True,
                'message': '签到成功，已加入等待队列',
                'practice_time': next_practice.start_time.strftime('%H:%M'),
                'piano_number': next_practice.piano_number,
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
        
        try:
            # 尝试处理考勤二维码
            from mymanage.attendance.models import QRCode, AttendanceRecord, AttendanceSession
            
            # 检查二维码是否是有效的考勤码 - 先尝试使用uuid匹配
            qrcode = QRCode.objects.filter(uuid=qrcode_data).first()
            
            # 如果没找到，尝试使用code匹配
            if not qrcode:
                qrcode = QRCode.objects.filter(code=qrcode_data).first()
            
            if qrcode and qrcode.is_valid():
                # 获取关联的会话
                session = AttendanceSession.objects.filter(qrcode=qrcode).first()
                
                if not session:
                    return JsonResponse({
                        'success': False,
                        'message': '二维码未关联到有效的考勤会话'
                    })
                
                # 检查学生是否已经签到
                existing_record = AttendanceRecord.objects.filter(
                    student=student,
                    session=session
                ).exists()
                
                if existing_record:
                    return JsonResponse({
                        'success': False,
                        'message': '您已经签到过此课程'
                    })
                
                # 检查学生是否属于该课程
                if student not in session.course.students.all():
                    return JsonResponse({
                        'success': False,
                        'message': '您不是此课程的学生'
                    })
                
                # 创建考勤记录
                from mymanage.courses.models import Piano
                
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
                        status='checked_in'
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'签到成功！已分配{piano.number}号钢琴',
                        'piano_number': piano.number
                    })
                else:
                    # 没有空闲钢琴，加入等待队列
                    from mymanage.attendance.models import WaitingQueue
                    
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
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'签到成功！已加入等待队列，预计等待{estimated_wait_time}分钟',
                        'waiting': True,
                        'wait_minutes': estimated_wait_time
                    })
            
            # 如果不是考勤二维码，尝试其他类型的处理（例如普通签到）
            try:
                # 处理JSON格式的二维码数据
                qr_data = json.loads(qrcode_data)
                
                # 验证二维码是否有效
                if qr_data.get('type') == 'attendance' and qr_data.get('valid'):
                    # 处理签到逻辑
                    return check_in(request)
                else:
                    return JsonResponse({
                        'success': False,
                        'message': '无效的二维码'
                    })
                    
            except json.JSONDecodeError:
                # 尝试当作普通签到处理
                if len(qrcode_data) > 0:
                    # 如果二维码包含某些特定标识，可以直接处理为普通签到
                    # 这里简单处理，非JSON格式且无法匹配为考勤二维码时当作普通签到
                    return check_in(request)
                else:
                    return JsonResponse({
                        'success': False,
                        'message': '无法识别的二维码格式'
                    })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'处理二维码时出错: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '请求方法错误'}, status=400)

@login_required
def practice_status(request):
    """获取当前练琴状态"""
    student = get_object_or_404(Student, user=request.user)
    today = timezone.now().date()
    
    # 获取今日练琴记录
    practice = PracticeRecord.objects.filter(
        student=student,
        date=today
    ).first()
    
    if not practice:
        return JsonResponse({
            'status': 'inactive',
            'message': '今日未签到'
        })
    
    now = timezone.now()
    
    if practice.start_time > now:
        # 在等待中
        wait_minutes = (practice.start_time - now).total_seconds() // 60
        return JsonResponse({
            'status': 'waiting',
            'message': '等待中',
            'start_time': practice.start_time.strftime('%H:%M'),
            'piano_number': practice.piano_number,
            'wait_minutes': int(wait_minutes)
        })
    elif practice.end_time > now:
        # 正在练琴
        elapsed = (now - practice.start_time).total_seconds() // 60
        remaining = (practice.end_time - now).total_seconds() // 60
        return JsonResponse({
            'status': 'active',
            'message': '练琴中',
            'piano_number': practice.piano_number,
            'elapsed_minutes': int(elapsed),
            'remaining_minutes': int(remaining)
        })
    else:
        # 已完成
        return JsonResponse({
            'status': 'completed',
            'message': '今日练琴已完成',
            'duration': practice.duration
        })

@login_required
def attendance(request):
    student = get_object_or_404(Student, user=request.user)
    today = timezone.now().date()
    
    # 获取今日考勤记录
    today_attendance = Attendance.objects.filter(
        student=student,
        date=today
    ).first()
    
    # 获取历史考勤记录
    attendances = Attendance.objects.filter(student=student).order_by('-date')
    paginator = Paginator(attendances, 10)
    page = request.GET.get('page')
    attendances = paginator.get_page(page)
    
    # 获取考勤统计数据
    total_days = attendances.count()
    present_days = attendances.filter(status='present').count()
    
    # 如果有历史记录，计算出勤率
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    # 获取本月考勤
    current_month = timezone.now().month
    current_year = timezone.now().year
    month_attendances = Attendance.objects.filter(
        student=student,
        date__month=current_month,
        date__year=current_year
    ).count()
    
    context = {
        'student': student,
        'today_attendance': today_attendance,
        'attendances': attendances,
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
    
    # 获取所有考勤记录
    attendances = Attendance.objects.filter(student=student).order_by('-date')
    
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
        
        month_count = Attendance.objects.filter(
            student=student,
            date__month=month,
            date__year=year
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
        
        week_count = Attendance.objects.filter(
            student=student,
            date__gte=start_date,
            date__lte=end_date
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
    
    # 处理搜索和筛选
    form = SheetMusicSearchForm(request.GET)
    sheet_music_list = SheetMusic.objects.filter(is_active=True)
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        difficulty = form.cleaned_data.get('difficulty')
        genre = form.cleaned_data.get('genre')
        
        if search_query:
            sheet_music_list = sheet_music_list.filter(
                title__icontains=search_query
            ) | sheet_music_list.filter(
                composer__icontains=search_query
            )
        
        if difficulty:
            sheet_music_list = sheet_music_list.filter(difficulty=difficulty)
        
        if genre:
            sheet_music_list = sheet_music_list.filter(genre=genre)
    
    # 分页
    paginator = Paginator(sheet_music_list, 9)
    page = request.GET.get('page')
    sheet_music_list = paginator.get_page(page)
    
    # 获取收藏的曲谱
    favorites = StudentFavorite.objects.filter(student=student).values_list('sheet_music_id', flat=True)
    
    context = {
        'student': student,
        'form': form,
        'sheet_music_list': sheet_music_list,
        'favorites': list(favorites),
    }
    return render(request, 'students/sheet_music.html', context)

@login_required
def sheet_music_detail(request, sheet_id):
    """曲谱详情页面"""
    student = get_object_or_404(Student, user=request.user)
    sheet = get_object_or_404(SheetMusic, id=sheet_id, is_active=True)
    
    # 检查是否收藏
    is_favorite = StudentFavorite.objects.filter(
        student=student,
        sheet_music=sheet
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
        sheet_music = get_object_or_404(SheetMusic, id=sheet_music_id)
        
        favorite, created = StudentFavorite.objects.get_or_create(
            student=student,
            sheet_music=sheet_music
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
    sheet = get_object_or_404(SheetMusic, id=sheet_id, is_active=True)
    
    # 检查是否收藏
    is_favorite = StudentFavorite.objects.filter(
        student=student,
        sheet_music=sheet
    ).exists()
    
    # 获取曲谱页面
    sheet_pages = []
    for page in sheet.sheet_pages.all().order_by('page_number'):
        sheet_pages.append({
            'page_number': page.page_number,
            'image_url': page.image.url if page.image else None
        })
    
    # 构建响应数据
    sheet_data = {
        'id': sheet.id,
        'title': sheet.title,
        'composer': sheet.composer,
        'difficulty': sheet.difficulty,
        'genre': sheet.genre,
        'description': sheet.description,
        'pdf_url': sheet.pdf_file.url if sheet.pdf_file else None,
        'upload_time': sheet.upload_time.strftime('%Y-%m-%d'),
        'pages': sheet_pages
    }
    
    return JsonResponse({
        'success': True,
        'sheet': sheet_data,
        'is_favorite': is_favorite
    })

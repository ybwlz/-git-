from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Piano, Course, CourseSchedule, SheetMusic, PianoLevel, PracticeSessionScheduler
from mymanage.attendance.models import AttendanceSession, AttendanceRecord, WaitingQueue
from mymanage.users.decorators import teacher_required
from mymanage.students.models import Student
from mymanage.teachers.models import TeacherProfile


@login_required
def piano_list(request):
    """查看所有钢琴列表"""
    pianos = Piano.objects.all()
    return render(request, 'courses/piano_list.html', {'pianos': pianos})


@login_required
def piano_detail(request, piano_id):
    """查看钢琴详情"""
    piano = get_object_or_404(Piano, id=piano_id)
    current_record = AttendanceRecord.objects.filter(piano=piano, status='checked_in').first()
    return render(request, 'courses/piano_detail.html', {
        'piano': piano,
        'current_record': current_record
    })


@teacher_required
def piano_manage(request, piano_id=None):
    """管理钢琴信息"""
    if piano_id:
        piano = get_object_or_404(Piano, id=piano_id)
        if request.method == 'POST':
            # 处理表单提交
            piano.brand = request.POST.get('brand')
            piano.model = request.POST.get('model')
            piano.is_active = 'is_active' in request.POST
            piano.notes = request.POST.get('notes')
            piano.save()
            messages.success(request, '钢琴信息已更新')
            return redirect('piano_list')
    else:
        piano = None
        if request.method == 'POST':
            # 创建新钢琴
            Piano.objects.create(
                number=request.POST.get('number'),
                brand=request.POST.get('brand'),
                model=request.POST.get('model'),
                is_active='is_active' in request.POST,
                notes=request.POST.get('notes')
            )
            messages.success(request, '新钢琴已添加')
            return redirect('piano_list')
    
    return render(request, 'courses/piano_manage.html', {'piano': piano})


@login_required
def sheet_music_list(request):
    """曲谱列表"""
    query = request.GET.get('q', '')
    level_id = request.GET.get('level', '')
    
    sheet_music = SheetMusic.objects.filter(is_public=True)
    
    if query:
        sheet_music = sheet_music.filter(
            Q(title__icontains=query) | 
            Q(composer__icontains=query) |
            Q(description__icontains=query)
        )
    
    if level_id:
        sheet_music = sheet_music.filter(level_id=level_id)
    
    # 分页
    paginator = Paginator(sheet_music, 12)  # 每页12个曲谱
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    levels = PianoLevel.objects.all()
    
    return render(request, 'courses/sheet_music_list.html', {
        'sheet_music': page_obj,
        'levels': levels,
        'query': query,
        'level_id': level_id
    })


@login_required
def sheet_music_detail(request, sheet_id):
    """曲谱详情"""
    sheet = get_object_or_404(SheetMusic, id=sheet_id)
    if not sheet.is_public and (not request.user.is_teacher and sheet.uploaded_by != request.user):
        messages.error(request, '您没有权限查看此曲谱')
        return redirect('sheet_music_list')
    
    return render(request, 'courses/sheet_music_detail.html', {'sheet': sheet})


@teacher_required
def sheet_music_manage(request, sheet_id=None):
    """管理曲谱"""
    if sheet_id:
        sheet = get_object_or_404(SheetMusic, id=sheet_id)
        if request.method == 'POST':
            # 处理更新
            sheet.title = request.POST.get('title')
            sheet.composer = request.POST.get('composer')
            sheet.level_id = request.POST.get('level')
            sheet.description = request.POST.get('description')
            sheet.is_public = 'is_public' in request.POST
            
            if 'file' in request.FILES:
                sheet.file = request.FILES['file']
            if 'cover_image' in request.FILES:
                sheet.cover_image = request.FILES['cover_image']
            
            sheet.save()
            messages.success(request, '曲谱已更新')
            return redirect('sheet_music_detail', sheet_id=sheet.id)
    else:
        sheet = None
        if request.method == 'POST':
            # 创建新曲谱
            new_sheet = SheetMusic(
                title=request.POST.get('title'),
                composer=request.POST.get('composer'),
                level_id=request.POST.get('level'),
                description=request.POST.get('description'),
                file=request.FILES.get('file'),
                uploaded_by=request.user,
                is_public='is_public' in request.POST
            )
            
            if 'cover_image' in request.FILES:
                new_sheet.cover_image = request.FILES['cover_image']
            
            new_sheet.save()
            messages.success(request, '曲谱已添加')
            return redirect('sheet_music_detail', sheet_id=new_sheet.id)
    
    levels = PianoLevel.objects.all()
    return render(request, 'courses/sheet_music_manage.html', {
        'sheet': sheet,
        'levels': levels
    })


@teacher_required
def delete_sheet_music(request, sheet_id):
    """删除曲谱"""
    sheet = get_object_or_404(SheetMusic, id=sheet_id)
    if request.method == 'POST':
        sheet.delete()
        messages.success(request, '曲谱已删除')
        return redirect('sheet_music_list')
    return render(request, 'courses/sheet_music_delete.html', {'sheet': sheet})


@login_required
def auto_scheduler_status(request):
    """获取自动排课状态"""
    # 获取当前用户的排课状态
    if hasattr(request.user, 'student'):
        student = request.user.student
        
        # 检查是否有活跃的考勤记录
        active_record = AttendanceRecord.objects.filter(
            student=student,
            status='checked_in'
        ).first()
        
        if active_record:
            # 学生已在练习
            return JsonResponse({
                'status': 'practicing',
                'piano': active_record.piano.number,
                'start_time': active_record.check_in_time.strftime('%H:%M:%S'),
                'session_id': active_record.session.id
            })
        
        # 检查是否在队列中
        current_session = AttendanceSession.objects.filter(status='active').first()
        if not current_session:
            return JsonResponse({'status': 'no_active_session'})
        
        waiting_record = WaitingQueue.objects.filter(
            student=student,
            session=current_session,
            is_active=True
        ).first()
        
        if waiting_record:
            # 在队列中等待
            position = PracticeSessionScheduler.get_queue_position(
                current_session.id, student.id
            )
            wait_time = PracticeSessionScheduler.calculate_wait_time(position)
            
            return JsonResponse({
                'status': 'waiting',
                'position': position + 1,  # 显示给用户的位置从1开始
                'estimated_wait_time': wait_time,
                'session_id': current_session.id
            })
        
        # 未在练习也未在队列中
        return JsonResponse({'status': 'not_in_queue'})
    
    return JsonResponse({'status': 'not_student'})


@login_required
def join_practice_queue(request):
    """加入练习队列"""
    if request.method == 'POST' and hasattr(request.user, 'student'):
        student = request.user.student
        
        # 获取活跃的考勤会话
        active_session = AttendanceSession.objects.filter(status='active').first()
        if not active_session:
            return JsonResponse({'success': False, 'message': '当前没有活跃的考勤会话'})
        
        # 检查学生是否已在队列中或已签到
        if AttendanceRecord.objects.filter(student=student, session=active_session, status='checked_in').exists():
            return JsonResponse({'success': False, 'message': '您已经签到并正在练习'})
        
        if WaitingQueue.objects.filter(student=student, session=active_session, is_active=True).exists():
            return JsonResponse({'success': False, 'message': '您已在等待队列中'})
        
        # 检查是否有可用钢琴
        available_piano = PracticeSessionScheduler.get_available_piano()
        
        if available_piano:
            # 有可用钢琴，直接签到
            available_piano.is_occupied = True
            available_piano.save()
            
            AttendanceRecord.objects.create(
                session=active_session,
                student=student,
                piano=available_piano,
                status='checked_in'
            )
            
            return JsonResponse({
                'success': True, 
                'status': 'assigned',
                'message': f'已为您分配钢琴 {available_piano.number} 号',
                'piano': available_piano.number
            })
        else:
            # 没有可用钢琴，加入等待队列
            waiting_queue_count = WaitingQueue.objects.filter(
                session=active_session,
                is_active=True
            ).count()
            
            wait_time = PracticeSessionScheduler.calculate_wait_time(waiting_queue_count)
            
            WaitingQueue.objects.create(
                session=active_session,
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
    
    return JsonResponse({'success': False, 'message': '无效的请求'})


@login_required
def check_out(request):
    """签退"""
    if request.method == 'POST' and hasattr(request.user, 'student'):
        student = request.user.student
        
        # 查找学生的活跃考勤记录
        active_record = AttendanceRecord.objects.filter(
            student=student,
            status='checked_in'
        ).first()
        
        if not active_record:
            return JsonResponse({'success': False, 'message': '没有找到您的活跃练习记录'})
        
        # 执行签退
        active_record.check_out()
        
        return JsonResponse({
            'success': True,
            'message': '签退成功，感谢您的练习！',
            'duration': str(active_record.duration)
        })
    
    return JsonResponse({'success': False, 'message': '无效的请求'})

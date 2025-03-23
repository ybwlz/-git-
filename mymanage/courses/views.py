from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
import datetime

from .models import Course, CourseSchedule, Enrollment, Piano, SheetMusic
from .forms import (
    CourseForm, CourseScheduleForm, EnrollmentForm,
    PianoForm, SheetMusicForm, SheetMusicSearchForm
)
from mymanage.students.models import Student
from mymanage.teachers.models import Teacher


@login_required
def course_list(request):
    """
    课程列表页面
    """
    # 获取所有课程并应用筛选条件
    courses = Course.objects.all()
    
    # 搜索过滤
    search_query = request.GET.get('q', '')
    if search_query:
        courses = courses.filter(
            Q(name__icontains=search_query) | 
            Q(code__icontains=search_query) |
            Q(teacher__name__icontains=search_query)
        )
    
    # 级别过滤
    level_filter = request.GET.get('level', '')
    if level_filter:
        courses = courses.filter(level=level_filter)
    
    # 状态过滤
    status_filter = request.GET.get('status', '')
    if status_filter:
        courses = courses.filter(status=status_filter)
    
    # 分页
    paginator = Paginator(courses, 10)  # 每页10条
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取级别和状态选项用于过滤器
    level_choices = Course.LEVEL_CHOICES
    status_choices = Course.COURSE_STATUS_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'level_filter': level_filter,
        'status_filter': status_filter,
        'level_choices': level_choices,
        'status_choices': status_choices,
    }
    
    return render(request, 'courses/course_list.html', context)


@login_required
def course_detail(request, pk):
    """
    课程详情页面
    """
    course = get_object_or_404(Course, pk=pk)
    
    # 获取课程安排
    schedules = course.schedules.all().order_by('weekday', 'start_time')
    
    # 获取已报名学生
    enrollments = course.enrollments.filter(status='active')
    
    # 获取相同级别的曲谱
    related_sheets = SheetMusic.objects.filter(level=course.level)
    
    context = {
        'course': course,
        'schedules': schedules,
        'enrollments': enrollments,
        'available_seats': course.get_available_seats(),
        'related_sheets': related_sheets,
    }
    
    # 如果当前用户是学生，检查是否已报名此课程
    if hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
        enrolled = Enrollment.objects.filter(
            student=student, 
            course=course, 
            status='active'
        ).exists()
        context['enrolled'] = enrolled
    
    return render(request, 'courses/course_detail.html', context)


@login_required
def course_create(request):
    """
    创建课程页面，仅管理员和教师可用
    """
    if not (request.user.is_staff or hasattr(request.user, 'teacher_profile')):
        messages.error(request, '您没有权限创建课程')
        return redirect('courses:list')
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'成功创建课程: {course.name}')
            return redirect('courses:detail', pk=course.id)
    else:
        # 如果是教师用户，自动设置教师字段
        initial = {}
        if hasattr(request.user, 'teacher_profile'):
            initial['teacher'] = request.user.teacher_profile
        
        form = CourseForm(initial=initial)
        
        # 如果是教师用户，限制只能选择自己
        if hasattr(request.user, 'teacher_profile') and not request.user.is_staff:
            form.fields['teacher'].queryset = Teacher.objects.filter(pk=request.user.teacher_profile.pk)
    
    return render(request, 'courses/course_form.html', {
        'form': form,
        'action': '创建课程'
    })


@login_required
def course_update(request, pk):
    """
    更新课程页面，仅课程教师和管理员可用
    """
    course = get_object_or_404(Course, pk=pk)
    
    # 权限检查
    if not (request.user.is_staff or 
            (hasattr(request.user, 'teacher_profile') and course.teacher == request.user.teacher_profile)):
        messages.error(request, '您没有权限编辑此课程')
        return redirect('courses:detail', pk=course.id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'成功更新课程: {course.name}')
            return redirect('courses:detail', pk=course.id)
    else:
        form = CourseForm(instance=course)
        
        # 如果是教师用户，限制只能选择自己
        if hasattr(request.user, 'teacher_profile') and not request.user.is_staff:
            form.fields['teacher'].queryset = Teacher.objects.filter(pk=request.user.teacher_profile.pk)
    
    return render(request, 'courses/course_form.html', {
        'form': form,
        'course': course,
        'action': '编辑课程'
    })


@login_required
def course_schedule_create(request, course_id):
    """
    创建课程安排，仅课程教师和管理员可用
    """
    course = get_object_or_404(Course, pk=course_id)
    
    # 权限检查
    if not (request.user.is_staff or 
            (hasattr(request.user, 'teacher_profile') and course.teacher == request.user.teacher_profile)):
        messages.error(request, '您没有权限为此课程创建安排')
        return redirect('courses:detail', pk=course_id)
    
    if request.method == 'POST':
        form = CourseScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, '成功创建课程安排')
            return redirect('courses:detail', pk=course_id)
    else:
        form = CourseScheduleForm(initial={'course': course})
        form.fields['course'].widget = forms.HiddenInput()
    
    return render(request, 'courses/schedule_form.html', {
        'form': form,
        'course': course,
        'action': '创建课程安排'
    })


@login_required
def course_schedule_update(request, pk):
    """
    更新课程安排，仅课程教师和管理员可用
    """
    schedule = get_object_or_404(CourseSchedule, pk=pk)
    course = schedule.course
    
    # 权限检查
    if not (request.user.is_staff or 
            (hasattr(request.user, 'teacher_profile') and course.teacher == request.user.teacher_profile)):
        messages.error(request, '您没有权限编辑此课程安排')
        return redirect('courses:detail', pk=course.id)
    
    if request.method == 'POST':
        form = CourseScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, '成功更新课程安排')
            return redirect('courses:detail', pk=course.id)
    else:
        form = CourseScheduleForm(instance=schedule)
        form.fields['course'].widget = forms.HiddenInput()
    
    return render(request, 'courses/schedule_form.html', {
        'form': form,
        'schedule': schedule,
        'course': course,
        'action': '编辑课程安排'
    })


@login_required
def enrollment_create(request, course_id=None):
    """
    学生报名课程
    """
    # 获取学生和课程
    student = None
    course = None
    
    if hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
    
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
    
    # 权限检查
    if not (request.user.is_staff or student):
        messages.error(request, '您无权进行报名操作')
        return redirect('courses:list')
    
    if request.method == 'POST':
        # 如果是学生用户，只能为自己报名
        if student and not request.user.is_staff:
            form = EnrollmentForm(request.POST, student=student)
        else:
            form = EnrollmentForm(request.POST)
            
        if form.is_valid():
            enrollment = form.save()
            messages.success(request, f'成功报名课程: {enrollment.course.name}')
            
            if student:
                return redirect('courses:my_courses')
            else:
                return redirect('courses:detail', pk=enrollment.course.id)
    else:
        initial = {}
        if student:
            initial['student'] = student
        if course:
            initial['course'] = course
            
        # 如果是学生用户，只能为自己报名
        if student and not request.user.is_staff:
            form = EnrollmentForm(initial=initial, student=student)
        else:
            form = EnrollmentForm(initial=initial)
    
    context = {
        'form': form,
        'action': '课程报名',
        'course': course
    }
    
    return render(request, 'courses/enrollment_form.html', context)


@login_required
def enrollment_update(request, pk):
    """
    更新报名状态，仅管理员可用
    """
    enrollment = get_object_or_404(Enrollment, pk=pk)
    
    # 权限检查
    if not request.user.is_staff:
        messages.error(request, '您没有权限更新报名状态')
        return redirect('courses:detail', pk=enrollment.course.id)
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, '成功更新报名状态')
            return redirect('courses:detail', pk=enrollment.course.id)
    else:
        form = EnrollmentForm(instance=enrollment)
    
    return render(request, 'courses/enrollment_form.html', {
        'form': form,
        'enrollment': enrollment,
        'action': '更新报名状态'
    })


@login_required
def my_courses(request):
    """
    我的课程页面，显示学生报名的课程或教师教授的课程
    """
    if hasattr(request.user, 'student_profile'):
        # 学生用户查看自己报名的课程
        student = request.user.student_profile
        enrollments = Enrollment.objects.filter(
            student=student,
            status='active'
        ).select_related('course')
        
        courses = [enrollment.course for enrollment in enrollments]
        
        # 获取今天的课程安排
        today = timezone.now().date()
        weekday = today.weekday()
        today_schedules = []
        
        for course in courses:
            schedules = course.schedules.filter(weekday=weekday)
            for schedule in schedules:
                today_schedules.append({
                    'course': course,
                    'schedule': schedule
                })
        
        # 按时间排序
        today_schedules.sort(key=lambda x: x['schedule'].start_time)
        
        return render(request, 'courses/my_courses_student.html', {
            'enrollments': enrollments,
            'today_schedules': today_schedules
        })
        
    elif hasattr(request.user, 'teacher_profile'):
        # 教师用户查看自己教授的课程
        teacher = request.user.teacher_profile
        courses = Course.objects.filter(teacher=teacher)
        
        # 获取今天的课程安排
        today = timezone.now().date()
        weekday = today.weekday()
        today_schedules = []
        
        for course in courses:
            schedules = course.schedules.filter(weekday=weekday)
            for schedule in schedules:
                today_schedules.append({
                    'course': course,
                    'schedule': schedule
                })
        
        # 按时间排序
        today_schedules.sort(key=lambda x: x['schedule'].start_time)
        
        return render(request, 'courses/my_courses_teacher.html', {
            'courses': courses,
            'today_schedules': today_schedules
        })
        
    else:
        messages.error(request, '您没有相关课程信息')
        return redirect('courses:list')


@login_required
def sheet_music_list(request):
    """
    曲谱列表页面
    """
    sheet_musics = SheetMusic.objects.all()
    
    # 搜索表单
    form = SheetMusicSearchForm(request.GET)
    if form.is_valid():
        title = form.cleaned_data.get('title')
        composer = form.cleaned_data.get('composer')
        level = form.cleaned_data.get('level')
        
        if title:
            sheet_musics = sheet_musics.filter(title__icontains=title)
        if composer:
            sheet_musics = sheet_musics.filter(composer__icontains=composer)
        if level:
            sheet_musics = sheet_musics.filter(level=level)
    
    # 分页
    paginator = Paginator(sheet_musics, 12)  # 每页12条
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取级别选项
    level_choices = SheetMusic.LEVEL_CHOICES
    
    return render(request, 'courses/sheet_music_list.html', {
        'page_obj': page_obj,
        'form': form,
        'level_choices': level_choices
    })


@login_required
def sheet_music_detail(request, pk):
    """
    曲谱详情页面
    """
    sheet_music = get_object_or_404(SheetMusic, pk=pk)
    
    # 获取相同级别的其他曲谱
    related_sheets = SheetMusic.objects.filter(level=sheet_music.level).exclude(pk=pk)[:5]
    
    return render(request, 'courses/sheet_music_detail.html', {
        'sheet_music': sheet_music,
        'related_sheets': related_sheets
    })


@login_required
def sheet_music_create(request):
    """
    创建曲谱页面，仅教师和管理员可用
    """
    if not (request.user.is_staff or hasattr(request.user, 'teacher_profile')):
        messages.error(request, '您没有权限上传曲谱')
        return redirect('courses:sheet_music_list')
    
    teacher = None
    if hasattr(request.user, 'teacher_profile'):
        teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        form = SheetMusicForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            sheet_music = form.save()
            messages.success(request, f'成功上传曲谱: {sheet_music.title}')
            return redirect('courses:sheet_music_detail', pk=sheet_music.id)
    else:
        form = SheetMusicForm(teacher=teacher)
    
    return render(request, 'courses/sheet_music_form.html', {
        'form': form,
        'action': '上传曲谱'
    })


@login_required
def sheet_music_update(request, pk):
    """
    更新曲谱页面，仅上传者和管理员可用
    """
    sheet_music = get_object_or_404(SheetMusic, pk=pk)
    
    # 权限检查
    if not (request.user.is_staff or 
            (hasattr(request.user, 'teacher_profile') and sheet_music.uploaded_by == request.user.teacher_profile)):
        messages.error(request, '您没有权限编辑此曲谱')
        return redirect('courses:sheet_music_detail', pk=pk)
    
    if request.method == 'POST':
        form = SheetMusicForm(request.POST, request.FILES, instance=sheet_music)
        if form.is_valid():
            form.save()
            messages.success(request, f'成功更新曲谱: {sheet_music.title}')
            return redirect('courses:sheet_music_detail', pk=pk)
    else:
        form = SheetMusicForm(instance=sheet_music)
    
    return render(request, 'courses/sheet_music_form.html', {
        'form': form,
        'sheet_music': sheet_music,
        'action': '编辑曲谱'
    })


@login_required
def piano_list(request):
    """
    钢琴列表页面，仅管理员可用
    """
    if not request.user.is_staff:
        messages.error(request, '您无权访问此页面')
        return redirect('courses:list')
    
    pianos = Piano.objects.all().order_by('piano_number')
    
    return render(request, 'courses/piano_list.html', {
        'pianos': pianos
    })


@login_required
def piano_update(request, pk):
    """
    更新钢琴信息，仅管理员可用
    """
    if not request.user.is_staff:
        messages.error(request, '您无权访问此页面')
        return redirect('courses:piano_list')
    
    piano = get_object_or_404(Piano, pk=pk)
    
    if request.method == 'POST':
        form = PianoForm(request.POST, instance=piano)
        if form.is_valid():
            form.save()
            messages.success(request, f'成功更新钢琴{piano.piano_number}号信息')
            return redirect('courses:piano_list')
    else:
        form = PianoForm(instance=piano)
    
    return render(request, 'courses/piano_form.html', {
        'form': form,
        'piano': piano,
        'action': '编辑钢琴信息'
    })


def initialize_pianos(request):
    """
    初始化钢琴数据，确保系统中有7台钢琴
    """
    if not request.user.is_superuser:
        messages.error(request, '只有超级管理员可以执行此操作')
        return redirect('courses:piano_list')
    
    # 检查是否已经有钢琴数据
    existing_pianos = Piano.objects.all()
    if existing_pianos.count() > 0:
        messages.warning(request, '已存在钢琴数据，无需初始化')
        return redirect('courses:piano_list')
    
    # 创建7台钢琴
    for i in range(1, 8):
        Piano.objects.create(
            piano_number=i,
            location='苗韵琴行教室',
            is_occupied=False
        )
    
    messages.success(request, '成功初始化7台钢琴数据')
    return redirect('courses:piano_list')

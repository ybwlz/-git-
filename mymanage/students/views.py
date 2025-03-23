from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
import pandas as pd
import xlwt
import io
import csv
from datetime import datetime, timedelta

from mymanage.users.models import User
from mymanage.courses.models import Course, Enrollment
from mymanage.scores.models import Score
from mymanage.attendance.models import AttendanceRecord
from .models import Student, StudentNotes
from .forms import (
    StudentForm, UserCreationWithStudentForm, StudentBulkImportForm,
    StudentNotesForm, StudentSearchForm
)


@login_required
def student_list(request):
    """
    学生列表视图
    """
    # 仅管理员和教师可以访问学生列表
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, '您没有权限访问该页面')
        return redirect('index')
    
    form = StudentSearchForm(request.GET or None)
    
    # 按照条件筛选学生
    students = Student.objects.all()
    
    # 教师只能看到自己教授课程的学生
    if request.user.user_type == 'teacher':
        teacher_courses = Course.objects.filter(teacher=request.user.teacher)
        students = Student.objects.filter(
            enrollments__course__in=teacher_courses,
            enrollments__status='active'
        ).distinct()
    
    # 应用搜索过滤
    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        gender = form.cleaned_data.get('gender')
        is_active = form.cleaned_data.get('is_active')
        join_date_start = form.cleaned_data.get('join_date_start')
        join_date_end = form.cleaned_data.get('join_date_end')
        
        if keyword:
            students = students.filter(
                Q(name__icontains=keyword) | 
                Q(student_id__icontains=keyword) | 
                Q(parent_name__icontains=keyword)
            )
            
        if gender:
            students = students.filter(gender=gender)
            
        if is_active:
            is_active_bool = is_active == '1'
            students = students.filter(is_active=is_active_bool)
            
        if join_date_start:
            students = students.filter(join_date__gte=join_date_start)
            
        if join_date_end:
            students = students.filter(join_date__lte=join_date_end)
    
    # 分页处理
    paginator = Paginator(students, 15)  # 每页显示15条记录
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'is_search': len(request.GET) > 0,
        'active_count': Student.objects.filter(is_active=True).count(),
        'inactive_count': Student.objects.filter(is_active=False).count(),
        'total_count': Student.objects.count()
    }
    
    # 处理导出请求
    if 'export' in request.GET:
        return export_students(request, students)
    
    return render(request, 'students/student_list.html', context)


@login_required
def student_create(request):
    """
    创建学生视图
    """
    # 仅管理员可以添加学生
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限添加学生')
        return redirect('students:list')
        
    if request.method == 'POST':
        form = UserCreationWithStudentForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'学生账户"{user.username}"创建成功！')
            return redirect('students:list')
    else:
        form = UserCreationWithStudentForm()
        
    context = {
        'form': form,
        'title': '添加学生账户'
    }
    return render(request, 'students/student_form.html', context)


@login_required
def student_edit(request, pk):
    """
    编辑学生信息视图
    """
    student = get_object_or_404(Student, pk=pk)
    
    # 仅管理员和教师可以编辑学生信息
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, '您没有权限编辑学生信息')
        return redirect('students:list')
        
    # 教师只能编辑自己教授课程的学生
    if request.user.user_type == 'teacher':
        teacher_courses = Course.objects.filter(teacher=request.user.teacher)
        if not Enrollment.objects.filter(
            student=student,
            course__in=teacher_courses,
            status='active'
        ).exists():
            messages.error(request, '您没有权限编辑该学生的信息')
            return redirect('students:list')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f'学生"{student.name}"的信息已更新')
            return redirect('students:detail', pk=student.pk)
    else:
        form = StudentForm(instance=student)
        
    context = {
        'form': form,
        'student': student,
        'title': f'编辑学生 - {student.name}'
    }
    return render(request, 'students/student_form.html', context)


@login_required
def student_detail(request, pk):
    """
    学生详情视图
    """
    student = get_object_or_404(Student, pk=pk)
    
    # 检查访问权限
    if request.user.user_type == 'student' and request.user.id != student.user.id:
        messages.error(request, '您没有权限查看其他学生的信息')
        return redirect('index')
        
    if request.user.user_type == 'teacher':
        teacher_courses = Course.objects.filter(teacher=request.user.teacher)
        if not Enrollment.objects.filter(
            student=student,
            course__in=teacher_courses
        ).exists():
            messages.error(request, '您没有权限查看该学生的信息')
            return redirect('students:list')
    
    # 获取学生的课程
    enrollments = Enrollment.objects.filter(student=student)
    
    # 获取学生的笔记
    notes = StudentNotes.objects.filter(student=student)
    
    # 获取学生最近的成绩
    recent_scores = Score.objects.filter(student=student).order_by('-exam__exam_date')[:5]
    
    # 获取学生最近的考勤记录
    recent_attendances = AttendanceRecord.objects.filter(student=student).order_by('-check_in_time')[:10]
    
    # 统计考勤记录
    attendance_stats = {
        'present': AttendanceRecord.objects.filter(student=student, status='checked_in').count(),
        'absent': AttendanceRecord.objects.filter(student=student, status='checked_out').count(),
        'late': 0,  # 此字段在新模型中不存在，设为0
    }
    
    # 处理添加笔记的表单
    if request.method == 'POST':
        notes_form = StudentNotesForm(request.POST)
        if notes_form.is_valid():
            note = notes_form.save(commit=False)
            note.student = student
            note.created_by = request.user
            note.save()
            messages.success(request, '笔记添加成功')
            return redirect('students:detail', pk=student.pk)
    else:
        notes_form = StudentNotesForm()
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'notes': notes,
        'notes_form': notes_form,
        'recent_scores': recent_scores,
        'recent_attendances': recent_attendances,
        'attendance_stats': attendance_stats
    }
    return render(request, 'students/student_detail.html', context)


@login_required
def student_delete_note(request, student_pk, note_pk):
    """
    删除学生笔记视图
    """
    note = get_object_or_404(StudentNotes, pk=note_pk, student_id=student_pk)
    
    # 检查权限 - 只有笔记的创建者或管理员可以删除笔记
    if request.user.user_type != 'admin' and note.created_by != request.user:
        messages.error(request, '您没有权限删除这条笔记')
        return redirect('students:detail', pk=student_pk)
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, '笔记已成功删除')
        return redirect('students:detail', pk=student_pk)
    
    context = {
        'note': note,
        'student': note.student
    }
    return render(request, 'students/confirm_delete_note.html', context)


@login_required
def student_profile(request):
    """
    当前学生个人资料视图
    """
    # 只有学生可以查看自己的个人资料
    if request.user.user_type != 'student':
        messages.error(request, '此页面只对学生开放')
        return redirect('index')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, '找不到学生资料')
        return redirect('index')
    
    # 获取学生的课程
    enrollments = Enrollment.objects.filter(student=student)
    
    # 获取学生的考勤统计
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    attendances = AttendanceRecord.objects.filter(student=student)
    month_attendances = attendances.filter(check_in_time__date__gte=month_start, check_in_time__date__lte=today)
    
    attendance_stats = {
        'total': attendances.count(),
        'present': attendances.filter(status='checked_in').count(),
        'absent': attendances.filter(status='checked_out').count(),
        'late': 0,
        'month_total': month_attendances.count(),
        'month_present': month_attendances.filter(status='checked_in').count()
    }
    
    # 获取学生的成绩统计
    scores = Score.objects.filter(student=student)
    score_stats = {
        'total': scores.count(),
        'average': scores.count() > 0 and sum(s.score for s in scores) / scores.count() or 0,
        'highest': scores.count() > 0 and max(s.score for s in scores) or 0,
        'passed': sum(1 for s in scores if s.score >= 60),
        'excellent': sum(1 for s in scores if s.score >= 85),
    }
    
    # 获取近期的考勤和成绩记录
    recent_attendances = attendances.order_by('-check_in_time')[:5]
    recent_scores = scores.order_by('-exam__exam_date')[:5]
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'attendance_stats': attendance_stats,
        'score_stats': score_stats,
        'recent_attendances': recent_attendances,
        'recent_scores': recent_scores
    }
    return render(request, 'students/student_profile.html', context)


@login_required
def student_bulk_import(request):
    """
    批量导入学生视图
    """
    # 仅管理员可以批量导入学生
    if request.user.user_type != 'admin':
        messages.error(request, '您没有权限导入学生')
        return redirect('students:list')
    
    if request.method == 'POST':
        form = StudentBulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            
            # 根据文件类型使用不同的导入方法
            if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
                import_result = import_students_from_excel(file)
            elif file.name.endswith('.csv'):
                import_result = import_students_from_csv(file)
            else:
                messages.error(request, '不支持的文件格式，请上传Excel或CSV文件')
                return redirect('students:bulk_import')
            
            # 处理导入结果
            if import_result['success']:
                messages.success(
                    request, 
                    f'成功导入 {import_result["success_count"]} 名学生'
                )
                if import_result['error_count'] > 0:
                    messages.warning(
                        request, 
                        f'导入过程中有 {import_result["error_count"]} 条记录出现错误'
                    )
                return redirect('students:list')
            else:
                messages.error(request, '导入失败：' + import_result['error_message'])
    else:
        form = StudentBulkImportForm()
    
    context = {
        'form': form,
        'title': '批量导入学生'
    }
    return render(request, 'students/student_bulk_import.html', context)


def import_students_from_excel(file):
    """
    从Excel文件导入学生
    """
    try:
        df = pd.read_excel(file)
        
        # 检查必要的列是否存在
        required_columns = ['学号', '姓名', '性别', '家长姓名', '家长电话']
        for col in required_columns:
            if col not in df.columns:
                return {
                    'success': False,
                    'error_message': f'Excel文件缺少必要的列: {col}'
                }
                
        success_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            try:
                # 创建用户账户
                student_id = str(row['学号'])
                username = f'student_{student_id}'
                user = User.objects.create_user(
                    username=username,
                    password=student_id,  # 初始密码设为学号
                    user_type='student'
                )
                
                # 创建学生资料
                student = Student.objects.create(
                    user=user,
                    student_id=student_id,
                    name=row['姓名'],
                    gender=row['性别'],
                    parent_name=row['家长姓名'],
                    parent_phone=str(row['家长电话']),
                )
                
                # 如果有出生日期，设置出生日期
                if '出生日期' in df.columns and pd.notna(row['出生日期']):
                    student.birth_date = row['出生日期']
                    student.save()
                
                success_count += 1
            except Exception as e:
                error_count += 1
                continue
        
        return {
            'success': True,
            'success_count': success_count,
            'error_count': error_count
        }
        
    except Exception as e:
        return {
            'success': False,
            'error_message': str(e)
        }


def import_students_from_csv(file):
    """
    从CSV文件导入学生
    """
    try:
        csv_data = file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_data))
        
        # 检查必要的列是否存在
        required_columns = ['学号', '姓名', '性别', '家长姓名', '家长电话']
        for col in required_columns:
            if col not in reader.fieldnames:
                return {
                    'success': False,
                    'error_message': f'CSV文件缺少必要的列: {col}'
                }
        
        success_count = 0
        error_count = 0
        
        for row in reader:
            try:
                # 创建用户账户
                student_id = str(row['学号'])
                username = f'student_{student_id}'
                user = User.objects.create_user(
                    username=username,
                    password=student_id,  # 初始密码设为学号
                    user_type='student'
                )
                
                # 创建学生资料
                student = Student.objects.create(
                    user=user,
                    student_id=student_id,
                    name=row['姓名'],
                    gender=row['性别'],
                    parent_name=row['家长姓名'],
                    parent_phone=str(row['家长电话']),
                )
                
                # 如果有出生日期，设置出生日期
                if '出生日期' in row and row['出生日期']:
                    try:
                        birth_date = datetime.strptime(row['出生日期'], '%Y-%m-%d').date()
                        student.birth_date = birth_date
                        student.save()
                    except:
                        pass
                
                success_count += 1
            except Exception as e:
                error_count += 1
                continue
        
        return {
            'success': True,
            'success_count': success_count,
            'error_count': error_count
        }
        
    except Exception as e:
        return {
            'success': False,
            'error_message': str(e)
        }


def export_students(request, students):
    """
    导出学生数据
    """
    # 确定导出格式
    export_format = request.GET.get('format', 'excel')
    
    if export_format == 'excel':
        # 创建Excel工作簿
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('学生列表')
        
        # 设置标题行样式
        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        
        # 写入标题行
        columns = ['学号', '姓名', '性别', '出生日期', '家长姓名', '家长电话', '地址', '入学日期', '状态']
        for col_num, column_title in enumerate(columns):
            ws.write(0, col_num, column_title, font_style)
        
        # 写入数据行
        row_num = 1
        for student in students:
            row = [
                student.student_id,
                student.name,
                student.get_gender_display(),
                student.birth_date.strftime('%Y-%m-%d') if student.birth_date else '',
                student.parent_name,
                student.parent_phone,
                student.address,
                student.join_date.strftime('%Y-%m-%d'),
                '活跃' if student.is_active else '不活跃'
            ]
            
            for col_num, cell_value in enumerate(row):
                ws.write(row_num, col_num, cell_value)
            row_num += 1
        
        # 创建HTTP响应，并设置Excel头信息
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="students.xls"'
        
        # 保存工作簿到响应
        wb.save(response)
        return response
    
    elif export_format == 'csv':
        # 创建CSV响应
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students.csv"'
        
        # 创建CSV写入器
        writer = csv.writer(response)
        
        # 写入标题行
        writer.writerow(['学号', '姓名', '性别', '出生日期', '家长姓名', '家长电话', '地址', '入学日期', '状态'])
        
        # 写入数据行
        for student in students:
            writer.writerow([
                student.student_id,
                student.name,
                student.get_gender_display(),
                student.birth_date.strftime('%Y-%m-%d') if student.birth_date else '',
                student.parent_name,
                student.parent_phone,
                student.address,
                student.join_date.strftime('%Y-%m-%d'),
                '活跃' if student.is_active else '不活跃'
            ])
        
        return response
    
    else:
        messages.error(request, '不支持的导出格式')
        return redirect('students:list')

# 添加一个学生档案创建辅助函数
def create_student_profile(user, student_id=None):
    """
    为指定用户创建基本的学生档案
    
    Args:
        user: 用户对象
        student_id: 可选学生ID，如不提供则使用用户名
        
    Returns:
        创建的学生实例
    """
    from mymanage.students.models import Student
    
    # 如果未提供学号，则使用用户名作为临时学号
    if not student_id:
        student_id = f"TEMP_{user.username}"
    
    # 创建基本学生档案
    student = Student.objects.create(
        user=user,
        student_id=student_id,
        name=user.get_full_name() or user.username,  # 如果没有全名则使用用户名
        parent_phone="未设置"  # 必填字段，设置默认值
    )
    
    return student

@login_required
def student_practice(request):
    """
    学生练习页面视图
    """
    # 只有学生可以查看练习页面
    if request.user.user_type != 'student':
        messages.error(request, '此页面只对学生开放')
        return redirect('index')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, '找不到学生资料')
        return redirect('index')
    
    # 在这里添加练习相关的逻辑
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/student_practice.html', context)

@login_required
def student_exam(request):
    """
    学生考勤记录视图
    """
    # 只有学生可以查看自己的考勤记录
    if request.user.user_type != 'student':
        messages.error(request, '此页面只对学生开放')
        return redirect('index')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, '找不到学生资料')
        return redirect('index')
    
    # 获取学生的考勤记录
    attendances = AttendanceRecord.objects.filter(student=student).order_by('-check_in_time')
    
    context = {
        'student': student,
        'attendances': attendances,
    }
    
    return render(request, 'students/student_attendance.html', context)

@login_required
def student_grades(request):
    """
    学生成绩/曲谱视图
    """
    # 只有学生可以查看自己的成绩/曲谱
    if request.user.user_type != 'student':
        messages.error(request, '此页面只对学生开放')
        return redirect('index')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, '找不到学生资料')
        return redirect('index')
    
    # 获取学生的曲谱列表（这里需要根据您的数据模型来调整）
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/sheet_music.html', context)
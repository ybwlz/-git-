from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Sum, F, Q, Max, Min
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
import json
import csv
from decimal import Decimal

from mymanage.students.models import Student
from mymanage.courses.models import Course, Enrollment
from .models import (
    ExamType, Exam, Score, ScoreDetail, 
    ScoreStatistics, PerformanceLevel
)
from .forms import (
    ExamTypeForm, ExamForm, ScoreForm, ScoreDetailForm, 
    ScoreDetailFormSet, BatchScoreForm, PerformanceLevelForm,
    ScoreSearchForm, ScoreStatisticsForm
)


@login_required
def exam_list(request):
    """
    考试列表视图
    """
    # 根据用户角色过滤不同的考试
    if request.user.user_type == 'admin':
        exams = Exam.objects.all().order_by('-exam_date', '-start_time')
    elif request.user.user_type == 'teacher':
        exams = Exam.objects.filter(teacher=request.user.teacher).order_by('-exam_date', '-start_time')
    else:
        # 学生只能看到自己课程的考试
        try:
            student = Student.objects.get(user=request.user)
            enrolled_courses = Course.objects.filter(enrollments__student=student)
            exams = Exam.objects.filter(course__in=enrolled_courses).order_by('-exam_date', '-start_time')
        except Student.DoesNotExist:
            exams = Exam.objects.none()
    
    # 分页处理
    paginator = Paginator(exams, 10)  # 每页显示10条记录
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'upcoming_exams': exams.filter(exam_date__gte=timezone.now().date(), status='pending').count(),
        'completed_exams': exams.filter(status='completed').count()
    }
    return render(request, 'scores/exam_list.html', context)


@login_required
def exam_create(request):
    """
    创建考试视图
    """
    # 检查权限，只有管理员和教师可以创建考试
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, '您没有权限创建考试')
        return redirect('scores:exam_list')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            messages.success(request, f'考试"{exam.name}"创建成功')
            return redirect('scores:exam_list')
    else:
        # 如果是教师，默认选择自己
        initial_data = {}
        if request.user.user_type == 'teacher':
            initial_data['teacher'] = request.user.teacher
        form = ExamForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': '创建新考试'
    }
    return render(request, 'scores/exam_form.html', context)


@login_required
def exam_edit(request, pk):
    """
    编辑考试视图
    """
    exam = get_object_or_404(Exam, pk=pk)
    
    # 检查权限，只有管理员和考试创建的教师可以编辑考试
    if request.user.user_type == 'admin' or (request.user.user_type == 'teacher' and exam.teacher == request.user.teacher):
        if request.method == 'POST':
            form = ExamForm(request.POST, instance=exam)
            if form.is_valid():
                exam = form.save()
                messages.success(request, f'考试"{exam.name}"更新成功')
                return redirect('scores:exam_list')
        else:
            form = ExamForm(instance=exam)
        
        context = {
            'form': form,
            'title': '编辑考试',
            'exam': exam
        }
        return render(request, 'scores/exam_form.html', context)
    else:
        messages.error(request, '您没有权限编辑此考试')
        return redirect('scores:exam_list')


@login_required
def exam_detail(request, pk):
    """
    考试详情视图
    """
    exam = get_object_or_404(Exam, pk=pk)
    
    # 获取考试的所有成绩
    scores = Score.objects.filter(exam=exam).order_by('student__name')
    
    # 计算统计数据
    total_students = scores.count()
    absent_students = scores.filter(is_absent=True).count()
    passed_students = scores.filter(score__gte=exam.passing_score).count()
    
    average_score = 0
    if total_students > 0:
        average_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
    
    # 获取最高分和最低分
    highest_score = 0
    highest_student = None
    lowest_score = exam.max_score
    lowest_student = None
    
    if total_students > 0:
        highest_score_obj = scores.order_by('-score').first()
        if highest_score_obj:
            highest_score = highest_score_obj.score
            highest_student = highest_score_obj.student
        
        lowest_score_obj = scores.order_by('score').first()
        if lowest_score_obj:
            lowest_score = lowest_score_obj.score
            lowest_student = lowest_score_obj.student
    
    # 分数分布统计
    score_distribution = [0] * 10  # 0-10, 10-20, ..., 90-100
    
    for score_obj in scores:
        if not score_obj.is_absent:  # 只统计参加考试的学生
            score_range = min(int(score_obj.score / 10), 9)  # 0-9
            score_distribution[score_range] += 1
    
    context = {
        'exam': exam,
        'scores': scores,
        'total_students': total_students,
        'absent_students': absent_students,
        'present_students': total_students - absent_students,
        'passed_students': passed_students,
        'pass_rate': (passed_students / (total_students - absent_students) * 100) if (total_students - absent_students) > 0 else 0,
        'average_score': average_score,
        'highest_score': highest_score,
        'highest_student': highest_student,
        'lowest_score': lowest_score,
        'lowest_student': lowest_student,
        'score_distribution': score_distribution,
        'score_ranges': ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100']
    }
    return render(request, 'scores/exam_detail.html', context)


@login_required
def score_list(request):
    """
    成绩列表视图
    """
    # 处理搜索表单
    form = ScoreSearchForm(request.GET or None)
    
    # 根据用户角色和搜索条件过滤不同的成绩
    scores = Score.objects.all()
    
    if request.user.user_type == 'admin':
        # 管理员可以看到所有成绩，但根据搜索条件过滤
        pass
    elif request.user.user_type == 'teacher':
        # 教师只能看到自己考试的成绩
        scores = scores.filter(exam__teacher=request.user.teacher)
    else:
        # 学生只能看到自己的成绩
        try:
            student = Student.objects.get(user=request.user)
            scores = scores.filter(student=student)
            # 学生不需要搜索自己
            form.fields.pop('student', None)
        except Student.DoesNotExist:
            scores = Score.objects.none()
    
    # 应用搜索过滤
    if form.is_valid():
        student = form.cleaned_data.get('student')
        course = form.cleaned_data.get('course')
        exam_type = form.cleaned_data.get('exam_type')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        min_score = form.cleaned_data.get('min_score')
        max_score = form.cleaned_data.get('max_score')
        
        if student:
            scores = scores.filter(student=student)
        if course:
            scores = scores.filter(exam__course=course)
        if exam_type:
            scores = scores.filter(exam__exam_type=exam_type)
        if start_date:
            scores = scores.filter(exam__exam_date__gte=start_date)
        if end_date:
            scores = scores.filter(exam__exam_date__lte=end_date)
        if min_score is not None:
            scores = scores.filter(score__gte=min_score)
        if max_score is not None:
            scores = scores.filter(score__lte=max_score)
    
    # 排序
    scores = scores.order_by('-exam__exam_date', 'student__name')
    
    # 分页处理
    paginator = Paginator(scores, 20)  # 每页显示20条记录
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'is_search': len(request.GET) > 0,
        'total_count': scores.count(),
        'average_score': scores.aggregate(avg=Avg('score'))['avg'] or 0
    }
    return render(request, 'scores/score_list.html', context)


@login_required
def score_create(request, exam_id=None):
    """
    创建成绩视图
    """
    # 检查权限，只有管理员和教师可以创建成绩
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, '您没有权限录入成绩')
        return redirect('scores:score_list')
    
    # 获取考试对象（如果提供了exam_id）
    exam = None
    if exam_id:
        exam = get_object_or_404(Exam, pk=exam_id)
        # 检查教师是否有权限为此考试录入成绩
        if request.user.user_type == 'teacher' and exam.teacher != request.user.teacher:
            messages.error(request, '您没有权限为此考试录入成绩')
            return redirect('scores:exam_detail', pk=exam_id)
    
    if request.method == 'POST':
        form = ScoreForm(request.POST, exam_id=exam_id)
        if form.is_valid():
            score = form.save(commit=False)
            score.created_by = request.user
            score.save()
            
            # 处理成绩详情
            formset = ScoreDetailFormSet(request.POST, instance=score)
            if formset.is_valid():
                formset.save()
            
            messages.success(request, f'学生"{score.student.name}"的成绩录入成功')
            
            # 重定向到考试详情页或继续添加
            if 'save_and_add' in request.POST:
                return redirect('scores:score_create', exam_id=exam_id)
            elif exam_id:
                return redirect('scores:exam_detail', pk=exam_id)
            else:
                return redirect('scores:score_list')
    else:
        form = ScoreForm(exam_id=exam_id)
        formset = ScoreDetailFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'exam': exam,
        'title': '录入学生成绩'
    }
    return render(request, 'scores/score_form.html', context)


@login_required
def score_edit(request, pk):
    """
    编辑成绩视图
    """
    score = get_object_or_404(Score, pk=pk)
    
    # 检查权限，只有管理员和考试的教师可以编辑成绩
    if request.user.user_type == 'admin' or (request.user.user_type == 'teacher' and score.exam.teacher == request.user.teacher):
        if request.method == 'POST':
            form = ScoreForm(request.POST, instance=score, exam_id=score.exam.id)
            if form.is_valid():
                score = form.save()
                
                # 处理成绩详情
                formset = ScoreDetailFormSet(request.POST, instance=score)
                if formset.is_valid():
                    formset.save()
                
                messages.success(request, f'学生"{score.student.name}"的成绩更新成功')
                return redirect('scores:exam_detail', pk=score.exam.id)
        else:
            form = ScoreForm(instance=score, exam_id=score.exam.id)
            formset = ScoreDetailFormSet(instance=score)
        
        context = {
            'form': form,
            'formset': formset,
            'score': score,
            'exam': score.exam,
            'title': '编辑学生成绩'
        }
        return render(request, 'scores/score_form.html', context)
    else:
        messages.error(request, '您没有权限编辑此成绩')
        return redirect('scores:score_list')


@login_required
def score_detail(request, pk):
    """
    成绩详情视图
    """
    score = get_object_or_404(Score, pk=pk)
    
    # 学生只能查看自己的成绩
    if request.user.user_type == 'student':
        try:
            student = Student.objects.get(user=request.user)
            if score.student != student:
                messages.error(request, '您没有权限查看此成绩')
                return redirect('scores:score_list')
        except Student.DoesNotExist:
            messages.error(request, '您没有权限查看此成绩')
            return redirect('scores:score_list')
    
    # 获取成绩详情
    score_details = score.details.all()
    
    # 获取表现等级
    performance_level = None
    try:
        performance_level = PerformanceLevel.objects.filter(
            min_score__lte=score.score,
            max_score__gte=score.score,
            is_active=True
        ).first()
    except:
        pass
    
    context = {
        'score': score,
        'score_details': score_details,
        'performance_level': performance_level
    }
    return render(request, 'scores/score_detail.html', context)


@login_required
def batch_score_create(request, exam_id):
    """
    批量录入成绩视图
    """
    # 检查权限，只有管理员和教师可以批量录入成绩
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, '您没有权限批量录入成绩')
        return redirect('scores:exam_list')
    
    exam = get_object_or_404(Exam, pk=exam_id)
    
    # 检查教师是否有权限为此考试录入成绩
    if request.user.user_type == 'teacher' and exam.teacher != request.user.teacher:
        messages.error(request, '您没有权限为此考试录入成绩')
        return redirect('scores:exam_list')
    
    if request.method == 'POST':
        form = BatchScoreForm(request.POST, initial={'exam': exam.id})
        if form.is_valid():
            # 获取所有学生并录入成绩
            exam = form.cleaned_data['exam']
            
            # 获取所有尚未录入成绩的学生
            enrolled_students = Student.objects.filter(
                enrollments__course=exam.course,
                enrollments__status='active'
            ).distinct()
            
            existing_student_ids = Score.objects.filter(exam=exam).values_list('student_id', flat=True)
            students_to_grade = enrolled_students.exclude(id__in=existing_student_ids)
            
            # 处理每个学生的成绩
            for student in students_to_grade:
                score_value = form.cleaned_data.get(f'score_{student.id}')
                is_absent = form.cleaned_data.get(f'absent_{student.id}', False)
                comment = form.cleaned_data.get(f'comment_{student.id}', '')
                
                # 如果提供了分数或标记为缺席，则创建成绩记录
                if score_value is not None or is_absent:
                    if is_absent:
                        score_value = 0
                    
                    Score.objects.create(
                        student=student,
                        exam=exam,
                        score=score_value,
                        is_absent=is_absent,
                        comment=comment,
                        created_by=request.user
                    )
            
            messages.success(request, f'考试"{exam.name}"的成绩批量录入成功')
            return redirect('scores:exam_detail', pk=exam.id)
    else:
        form = BatchScoreForm(initial={'exam': exam.id})
    
    context = {
        'form': form,
        'exam': exam,
        'title': '批量录入成绩'
    }
    return render(request, 'scores/batch_score_form.html', context)


@login_required
def statistics(request):
    """
    成绩统计视图
    """
    # 处理表单提交
    if request.method == 'POST':
        form = ScoreStatisticsForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            exam_type = form.cleaned_data['exam_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # 构建查询条件
            query = Q(exam__course=course)
            if exam_type:
                query &= Q(exam__exam_type=exam_type)
            if start_date:
                query &= Q(exam__exam_date__gte=start_date)
            if end_date:
                query &= Q(exam__exam_date__lte=end_date)
            
            # 查询符合条件的成绩
            scores = Score.objects.filter(query)
            
            # 基本统计数据
            exam_count = scores.values('exam').distinct().count()
            student_count = scores.values('student').distinct().count()
            
            # 平均分、最高分、最低分
            avg_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
            max_score = scores.aggregate(max=Max('score'))['max'] or 0
            min_score = scores.aggregate(min=Min('score'))['min'] or 0
            
            # 及格率和优秀率（假设60分及格，85分优秀）
            total_exams = scores.count()
            if total_exams > 0:
                pass_count = scores.filter(score__gte=60).count()
                excellent_count = scores.filter(score__gte=85).count()
                pass_rate = (pass_count / total_exams) * 100
                excellent_rate = (excellent_count / total_exams) * 100
            else:
                pass_rate = 0
                excellent_rate = 0
            
            # 成绩分布
            score_ranges = [
                {'range': '0-60', 'count': scores.filter(score__lt=60).count()},
                {'range': '60-70', 'count': scores.filter(score__gte=60, score__lt=70).count()},
                {'range': '70-80', 'count': scores.filter(score__gte=70, score__lt=80).count()},
                {'range': '80-90', 'count': scores.filter(score__gte=80, score__lt=90).count()},
                {'range': '90-100', 'count': scores.filter(score__gte=90).count()},
            ]
            
            # 按考试统计
            exam_stats = scores.values('exam__name', 'exam__exam_date').annotate(
                avg_score=Avg('score'),
                pass_rate=Sum(Case(When(score__gte=60, then=1), default=0)) * 100.0 / Count('id'),
                student_count=Count('id')
            ).order_by('exam__exam_date')
            
            # 按学生统计
            student_stats = scores.values('student__name').annotate(
                avg_score=Avg('score'),
                max_score=Max('score'),
                min_score=Min('score'),
                exam_count=Count('exam')
            ).order_by('-avg_score')
            
            # 保存统计结果
            statistics_obj, created = ScoreStatistics.objects.update_or_create(
                course=course,
                statistics_date=timezone.now().date(),
                defaults={
                    'exam_count': exam_count,
                    'student_count': student_count,
                    'average_score': avg_score,
                    'highest_score': max_score,
                    'lowest_score': min_score,
                    'pass_rate': pass_rate,
                    'excellent_rate': excellent_rate
                }
            )
            
            context = {
                'form': form,
                'course': course,
                'exam_type': exam_type,
                'start_date': start_date,
                'end_date': end_date,
                'statistics': {
                    'exam_count': exam_count,
                    'student_count': student_count,
                    'average_score': avg_score,
                    'highest_score': max_score,
                    'lowest_score': min_score,
                    'pass_rate': pass_rate,
                    'excellent_rate': excellent_rate,
                    'score_ranges': score_ranges,
                    'exam_stats': exam_stats,
                    'student_stats': student_stats
                }
            }
            return render(request, 'scores/statistics_result.html', context)
    else:
        form = ScoreStatisticsForm()
    
    context = {
        'form': form,
        'title': '成绩统计'
    }
    return render(request, 'scores/statistics_form.html', context)


@login_required
def student_scores(request, student_id):
    """
    查看学生的所有成绩
    """
    student = get_object_or_404(Student, pk=student_id)
    
    # 学生只能查看自己的成绩
    if request.user.user_type == 'student':
        try:
            user_student = Student.objects.get(user=request.user)
            if student != user_student:
                messages.error(request, '您没有权限查看其他学生的成绩')
                return redirect('scores:score_list')
        except Student.DoesNotExist:
            messages.error(request, '您没有权限查看此学生的成绩')
            return redirect('scores:score_list')
    
    # 教师只能查看自己课程的学生成绩
    if request.user.user_type == 'teacher':
        teacher_courses = Course.objects.filter(teacher=request.user.teacher)
        if not Enrollment.objects.filter(
            student=student,
            course__in=teacher_courses
        ).exists():
            messages.error(request, '您没有权限查看此学生的成绩')
            return redirect('scores:score_list')
    
    # 获取学生的所有成绩
    scores = Score.objects.filter(student=student).order_by('-exam__exam_date')
    
    # 计算统计数据
    total_exams = scores.count()
    total_score = scores.aggregate(sum=Sum('score'))['sum'] or 0
    average_score = total_score / total_exams if total_exams > 0 else 0
    
    # 计算及格率和优秀率
    if total_exams > 0:
        passed_exams = scores.filter(score__gte=60).count()
        excellent_exams = scores.filter(score__gte=85).count()
        pass_rate = (passed_exams / total_exams) * 100
        excellent_rate = (excellent_exams / total_exams) * 100
    else:
        pass_rate = 0
        excellent_rate = 0
    
    # 获取最高分和最低分
    highest_score = scores.order_by('-score').first()
    lowest_score = scores.order_by('score').first()
    
    # 按课程分组统计
    course_stats = scores.values('exam__course__name').annotate(
        avg_score=Avg('score'),
        max_score=Max('score'),
        min_score=Min('score'),
        exam_count=Count('exam')
    ).order_by('exam__course__name')
    
    context = {
        'student': student,
        'scores': scores,
        'total_exams': total_exams,
        'average_score': average_score,
        'pass_rate': pass_rate,
        'excellent_rate': excellent_rate,
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        'course_stats': course_stats
    }
    return render(request, 'scores/student_scores.html', context)


@login_required
def export_scores(request, exam_id):
    """
    导出考试成绩为CSV
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    
    # 检查权限，只有管理员和考试的教师可以导出成绩
    if not (request.user.user_type == 'admin' or (request.user.user_type == 'teacher' and exam.teacher == request.user.teacher)):
        messages.error(request, '您没有权限导出此考试成绩')
        return redirect('scores:exam_detail', pk=exam_id)
    
    # 获取所有成绩
    scores = Score.objects.filter(exam=exam).order_by('student__name')
    
    # 创建HTTP响应，并设置CSV头信息
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{exam.name}_scores.csv"'
    
    # 创建CSV写入器
    writer = csv.writer(response)
    
    # 写入标题行
    writer.writerow(['学生姓名', '分数', '是否缺席', '评语', '创建时间'])
    
    # 写入数据行
    for score in scores:
        writer.writerow([
            score.student.name,
            score.score,
            '是' if score.is_absent else '否',
            score.comment,
            score.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


@login_required
def ajax_get_performance_level(request):
    """
    AJAX请求：根据分数获取表现等级
    """
    score = request.GET.get('score')
    if not score:
        return JsonResponse({'error': '未提供分数'}, status=400)
    
    try:
        score_value = float(score)
        performance_level = PerformanceLevel.objects.filter(
            min_score__lte=score_value,
            max_score__gte=score_value,
            is_active=True
        ).first()
        
        if performance_level:
            return JsonResponse({
                'name': performance_level.name,
                'color': performance_level.color_code,
                'description': performance_level.description
            })
        else:
            return JsonResponse({'error': '没有找到对应的表现等级'}, status=404)
    except ValueError:
        return JsonResponse({'error': '分数格式不正确'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
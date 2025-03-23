from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64

from .models import Teacher, TeacherCertificate
from .forms import TeacherProfileForm, TeacherCertificateForm, TeacherRegistrationForm
from mymanage.students.models import Student
from mymanage.courses.models import Course, CourseSchedule
from mymanage.attendance.models import AttendanceRecord
from mymanage.finance.models import Payment
from mymanage.scores.models import Score
from mymanage.users.decorators import teacher_required


class TeacherDashboardView:
    """
    教师仪表盘视图类
    """
    @staticmethod
    @login_required
    @teacher_required
    def dashboard(request):
        teacher = request.user.teacher_profile
        
        # 获取今日课程
        today = timezone.now().date()
        today_schedules = CourseSchedule.objects.filter(
            teacher=teacher,
            date=today
        ).order_by('start_time')
        
        # 获取学生统计数据
        student_count = Student.objects.filter(
            course__teacher=teacher
        ).distinct().count()
        
        # 获取近30天考勤数据
        thirty_days_ago = today - timedelta(days=30)
        attendance_stats = AttendanceRecord.objects.filter(
            schedule__teacher=teacher,
            date__gte=thirty_days_ago
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late'))
        )
        
        # 获取本月收入统计
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_income = Payment.objects.filter(
            course__teacher=teacher,
            payment_date__month=current_month,
            payment_date__year=current_year
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        context = {
            'teacher': teacher,
            'today_schedules': today_schedules,
            'student_count': student_count,
            'attendance_stats': attendance_stats,
            'monthly_income': monthly_income,
        }
        
        return render(request, 'teachers/teacher_dashboard.html', context)


class TeacherProfileView:
    """
    教师个人资料视图类
    """
    @staticmethod
    @login_required
    @teacher_required
    def profile(request):
        teacher = request.user.teacher_profile
        certificates = TeacherCertificate.objects.filter(teacher=teacher)
        
        if request.method == 'POST':
            form = TeacherProfileForm(request.POST, instance=teacher)
            if form.is_valid():
                form.save()
                messages.success(request, '个人资料更新成功！')
                return redirect('teachers:profile')
        else:
            form = TeacherProfileForm(instance=teacher)
            
        context = {
            'teacher': teacher,
            'form': form,
            'certificates': certificates,
        }
        
        return render(request, 'teachers/teacher_profile.html', context)
    
    @staticmethod
    @login_required
    @teacher_required
    def add_certificate(request):
        teacher = request.user.teacher_profile
        
        if request.method == 'POST':
            form = TeacherCertificateForm(request.POST, request.FILES)
            if form.is_valid():
                certificate = form.save(commit=False)
                certificate.teacher = teacher
                certificate.save()
                messages.success(request, '证书添加成功！')
                return redirect('teachers:profile')
        else:
            form = TeacherCertificateForm()
            
        context = {
            'form': form,
        }
        
        return render(request, 'teachers/add_certificate.html', context)


class TeacherStudentManagementView:
    """
    教师学生管理视图类
    """
    @staticmethod
    @login_required
    @teacher_required
    def student_list(request):
        teacher = request.user.teacher_profile
        courses = Course.objects.filter(teacher=teacher)
        
        # 通过课程获取学生
        students = Student.objects.filter(
            course__teacher=teacher
        ).distinct()
        
        context = {
            'teacher': teacher,
            'students': students,
            'courses': courses,
        }
        
        return render(request, 'teachers/teacher_students.html', context)
    
    @staticmethod
    @login_required
    @teacher_required
    def student_detail(request, student_id):
        teacher = request.user.teacher_profile
        student = get_object_or_404(Student, id=student_id)
        
        # 检查该学生是否属于该教师的课程
        courses = Course.objects.filter(teacher=teacher, students=student)
        
        if not courses.exists():
            messages.error(request, '您无权查看此学生信息')
            return redirect('teachers:student_list')
        
        # 获取学生成绩
        scores = Score.objects.filter(student=student, course__in=courses)
        
        # 获取学生考勤
        attendances = AttendanceRecord.objects.filter(
            student=student,
            schedule__course__in=courses
        ).order_by('-date')
        
        context = {
            'teacher': teacher,
            'student': student,
            'courses': courses,
            'scores': scores,
            'attendances': attendances,
        }
        
        return render(request, 'teachers/student_detail.html', context)


class TeacherAttendanceView:
    """
    教师考勤管理视图类
    """
    @staticmethod
    @login_required
    @teacher_required
    def attendance_management(request):
        teacher = request.user.teacher_profile
        courses = Course.objects.filter(teacher=teacher)
        
        # 获取当前日期和时间
        current_date = timezone.now().date()
        
        # 获取今日课程安排
        today_schedules = CourseSchedule.objects.filter(
            teacher=teacher,
            date=current_date
        ).order_by('start_time')
        
        context = {
            'teacher': teacher,
            'courses': courses,
            'current_date': current_date,
            'today_schedules': today_schedules,
        }
        
        return render(request, 'teachers/teacher_attendance.html', context)
    
    @staticmethod
    @login_required
    @teacher_required
    def generate_qrcode(request, schedule_id):
        schedule = get_object_or_404(CourseSchedule, id=schedule_id, teacher=request.user.teacher_profile)
        
        # 创建二维码数据
        qr_data = {
            'schedule_id': schedule.id,
            'course_id': schedule.course.id,
            'teacher_id': schedule.teacher.id,
            'timestamp': datetime.now().timestamp()
        }
        
        # 将数据转换为字符串
        qr_string = f"schedule:{schedule.id}|course:{schedule.course.id}|teacher:{schedule.teacher.id}|time:{qr_data['timestamp']}"
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return JsonResponse({'qrcode': qr_image_base64})
    
    @staticmethod
    @login_required
    @teacher_required
    def attendance_record(request, course_id=None):
        teacher = request.user.teacher_profile
        
        if course_id:
            course = get_object_or_404(Course, id=course_id, teacher=teacher)
            attendances = AttendanceRecord.objects.filter(
                schedule__course=course
            ).order_by('-date')
        else:
            attendances = AttendanceRecord.objects.filter(
                schedule__teacher=teacher
            ).order_by('-date')
        
        context = {
            'teacher': teacher,
            'attendances': attendances,
        }
        
        return render(request, 'teachers/attendance_record.html', context)


class TeacherFinanceView:
    """
    教师财务管理视图类
    """
    @staticmethod
    @login_required
    @teacher_required
    def finance_management(request):
        teacher = request.user.teacher_profile
        
        # 获取教师的所有课程
        courses = Course.objects.filter(teacher=teacher)
        
        # 获取各课程的付款记录
        course_payments = {}
        total_income = 0
        
        for course in courses:
            payments = Payment.objects.filter(course=course)
            amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
            course_payments[course.id] = {
                'name': course.name,
                'amount': amount,
                'student_count': course.students.count(),
                'payments': payments
            }
            total_income += amount
        
        # 按月统计收入
        current_year = timezone.now().year
        monthly_income = []
        
        for month in range(1, 13):
            amount = Payment.objects.filter(
                course__teacher=teacher,
                payment_date__year=current_year,
                payment_date__month=month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            monthly_income.append({
                'month': month,
                'amount': amount
            })
        
        context = {
            'teacher': teacher,
            'courses': courses,
            'course_payments': course_payments,
            'total_income': total_income,
            'monthly_income': monthly_income,
        }
        
        return render(request, 'teachers/teacher_finance.html', context)


class TeacherSheetMusicView:
    """
    教师曲谱管理视图类
    """
    @staticmethod
    @login_required
    @teacher_required
    def sheet_music_management(request):
        teacher = request.user.teacher_profile
        # 这里需要定义SheetMusic模型，暂时用假数据
        sheet_music = []  # 待后续完善
        
        context = {
            'teacher': teacher,
            'sheet_music': sheet_music,
        }
        
        return render(request, 'teachers/teacher_sheet_music.html', context)


class TeacherCourseView:
    """
    教师课程管理视图类
    """
    @staticmethod
    @login_required
    @teacher_required
    def course_list(request):
        teacher = request.user.teacher_profile
        courses = Course.objects.filter(teacher=teacher)
        
        context = {
            'teacher': teacher,
            'courses': courses,
        }
        
        return render(request, 'teachers/teacher_courses.html', context)
    
    @staticmethod
    @login_required
    @teacher_required
    def course_detail(request, course_id):
        teacher = request.user.teacher_profile
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        # 获取课程学生
        students = course.students.all()
        
        # 获取课程安排
        schedules = CourseSchedule.objects.filter(course=course).order_by('date', 'start_time')
        
        context = {
            'teacher': teacher,
            'course': course,
            'students': students,
            'schedules': schedules,
        }
        
        return render(request, 'teachers/course_detail.html', context)


# 整合所有视图函数
teacher_dashboard = TeacherDashboardView.dashboard
teacher_profile = TeacherProfileView.profile
add_certificate = TeacherProfileView.add_certificate
student_list = TeacherStudentManagementView.student_list
student_detail = TeacherStudentManagementView.student_detail
attendance_management = TeacherAttendanceView.attendance_management
generate_qrcode = TeacherAttendanceView.generate_qrcode
attendance_record = TeacherAttendanceView.attendance_record
finance_management = TeacherFinanceView.finance_management
sheet_music_management = TeacherSheetMusicView.sheet_music_management
course_list = TeacherCourseView.course_list
course_detail = TeacherCourseView.course_detail

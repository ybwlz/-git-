from django.db import models
from mymanage.users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class Student(models.Model):
    LEVEL_CHOICES = [(i, f"{i}级") for i in range(1, 11)]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=50, verbose_name='姓名')
    level = models.IntegerField(choices=LEVEL_CHOICES, verbose_name='当前等级')
    target_level = models.IntegerField(choices=LEVEL_CHOICES, verbose_name='目标等级')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    parent_name = models.CharField(max_length=50, verbose_name='家长姓名')
    parent_phone = models.CharField(max_length=11, verbose_name='家长电话')
    school = models.CharField(max_length=100, verbose_name='就读学校')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '学生'
        verbose_name_plural = '学生'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_level_display()}"

# 添加信号处理器，自动将新创建的学生添加到默认课程
@receiver(post_save, sender=Student)
def add_student_to_default_course(sender, instance, created, **kwargs):
    """当新学生被创建时，自动将其添加到默认通用课程"""
    if created:  # 只在学生首次创建时执行
        from mymanage.courses.models import Course
        # 获取所有默认通用课程
        default_courses = Course.objects.filter(code='DEFAULT')
        # 将学生添加到所有默认课程
        for course in default_courses:
            course.students.add(instance)
            print(f"学生 {instance.name} 已自动添加到 {course.name} 课程")

class PracticeRecord(models.Model):
    """
    练琴记录模型，作为系统的主要考勤记录。
    这个模型既记录学生的练琴时间，又作为考勤记录使用。
    """
    STATUS_CHOICES = [
        ('active', '练琴中'),
        ('completed', '已完成'),
        ('cancelled', '已取消')
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='practice_records', verbose_name='学生')
    date = models.DateField(verbose_name='练习日期')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='练习时长(分钟)')
    piano_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)], verbose_name='钢琴编号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    # 新增字段，用于关联考勤会话
    attendance_session = models.ForeignKey('attendance.AttendanceSession', 
                                          on_delete=models.SET_NULL, 
                                          related_name='practice_records', 
                                          null=True, blank=True, 
                                          verbose_name='关联考勤会话')
    
    class Meta:
        verbose_name = '练琴记录'
        verbose_name_plural = '练琴记录'
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.student.name} - {self.date}"

    @property
    def check_in_time(self):
        """兼容AttendanceRecord API，返回开始时间"""
        return self.start_time
    
    @property
    def check_out_time(self):
        """兼容AttendanceRecord API，返回结束时间"""
        return self.end_time
    
    @property
    def duration_minutes(self):
        """兼容AttendanceRecord API，返回时长（分钟）"""
        return self.duration

# 以下是原来的Attendance模型，仅作为兼容保留，不再主动使用
class Attendance(models.Model):
    """
    旧版考勤记录，仅为兼容性保留，不再主动使用。
    新的考勤记录应该使用PracticeRecord。
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances', verbose_name='学生')
    date = models.DateField(verbose_name='考勤日期')
    check_in_time = models.DateTimeField(verbose_name='签到时间')
    check_out_time = models.DateTimeField(null=True, blank=True, verbose_name='签退时间')
    status = models.CharField(max_length=20, choices=[
        ('present', '已签到'),
        ('absent', '未签到'),
        ('late', '迟到'),
        ('early_leave', '早退')
    ], default='present', verbose_name='考勤状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '旧版考勤记录'
        verbose_name_plural = '旧版考勤记录'
        ordering = ['-date', '-check_in_time']

    def __str__(self):
        return f"{self.student.name} - {self.date}"

class SheetMusic(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', '初级'),
        ('intermediate', '中级'),
        ('advanced', '高级'),
    ]
    
    GENRE_CHOICES = [
        ('classical', '古典'),
        ('pop', '流行'),
        ('jazz', '爵士'),
        ('folk', '民谣'),
    ]

    title = models.CharField(max_length=100, verbose_name='曲谱名称')
    composer = models.CharField(max_length=100, verbose_name='作曲家')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, verbose_name='难度等级')
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, verbose_name='曲风分类')
    cover_image = models.ImageField(upload_to='sheet_music/covers/', verbose_name='封面图片')
    pdf_file = models.FileField(upload_to='sheet_music/pdfs/', verbose_name='PDF文件')
    description = models.TextField(blank=True, null=True, verbose_name='曲谱描述')
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    is_active = models.BooleanField(default=True, verbose_name='是否可用')

    class Meta:
        verbose_name = '曲谱'
        verbose_name_plural = '曲谱'
        ordering = ['-upload_time']

    def __str__(self):
        return f"{self.title} - {self.composer}"

class SheetMusicPage(models.Model):
    sheet_music = models.ForeignKey(SheetMusic, on_delete=models.CASCADE, related_name='sheet_pages', verbose_name='曲谱')
    page_number = models.IntegerField(verbose_name='页码')
    image = models.ImageField(upload_to='sheet_music/pages/', verbose_name='页面图片')
    
    class Meta:
        verbose_name = '曲谱页面'
        verbose_name_plural = '曲谱页面'
        ordering = ['sheet_music', 'page_number']
        unique_together = ['sheet_music', 'page_number']
    
    def __str__(self):
        return f"{self.sheet_music.title} - 第{self.page_number}页"

class StudentFavorite(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='favorites', verbose_name='学生')
    sheet_music = models.ForeignKey(SheetMusic, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='曲谱')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='收藏时间')

    class Meta:
        verbose_name = '学生收藏'
        verbose_name_plural = '学生收藏'
        unique_together = ['student', 'sheet_music']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.name} - {self.sheet_music.title}"

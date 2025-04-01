from django.db import models
from django.utils import timezone
# 避免循环导入，将Student导入放入函数内部
# from mymanage.students.models import Student
from mymanage.teachers.models import TeacherProfile
from django.core.exceptions import ValidationError
import datetime


class PianoLevel(models.Model):
    """钢琴等级模型"""
    LEVEL_CHOICES = [
        (1, '1级'),
        (2, '2级'),
        (3, '3级'),
        (4, '4级'),
        (5, '5级'),
        (6, '6级'),
        (7, '7级'),
        (8, '8级'),
        (9, '9级'),
        (10, '10级'),
    ]
    
    level = models.IntegerField('等级', choices=LEVEL_CHOICES, unique=True)
    description = models.TextField('描述', blank=True)
    
    class Meta:
        verbose_name = '钢琴等级'
        verbose_name_plural = '钢琴等级'
        ordering = ['level']
    
    def __str__(self):
        return f"{self.get_level_display()}"


class Piano(models.Model):
    """钢琴模型"""
    number = models.IntegerField('钢琴编号', unique=True)
    brand = models.CharField('品牌', max_length=50)
    model = models.CharField('型号', max_length=50)
    purchase_date = models.DateField('购买日期', null=True, blank=True)
    last_tuned_date = models.DateField('最后调音日期', null=True, blank=True)
    is_active = models.BooleanField('是否可用', default=True)
    is_occupied = models.BooleanField('是否被占用', default=False)
    notes = models.TextField('备注', blank=True)
    
    class Meta:
        verbose_name = '钢琴'
        verbose_name_plural = '钢琴'
        ordering = ['number']
    
    def __str__(self):
        return f"钢琴-{self.number}"
    
    def clean(self):
        """验证钢琴编号在1-7之间"""
        if self.number < 1 or self.number > 7:
            raise ValidationError('钢琴编号必须在1-7之间')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Course(models.Model):
    """课程模型（用于排课和考勤管理）"""
    name = models.CharField('课程名称', max_length=100)
    code = models.CharField('课程代码', max_length=20, unique=True)
    description = models.TextField('课程描述', blank=True)
    level = models.ForeignKey(PianoLevel, on_delete=models.CASCADE, related_name='courses', verbose_name='钢琴等级')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='courses', verbose_name='教师')
    duration = models.DurationField('标准练习时长', default=datetime.timedelta(minutes=30))
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    students = models.ManyToManyField('students.Student', related_name='courses', verbose_name='学生', blank=True)
    is_active = models.BooleanField('是否有效', default=True)
    
    class Meta:
        verbose_name = '课程'
        verbose_name_plural = '课程'
        ordering = ['level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.level})"


class CourseSchedule(models.Model):
    """课程安排模型"""
    WEEKDAY_CHOICES = [
        (0, '周一'),
        (1, '周二'),
        (2, '周三'),
        (3, '周四'),
        (4, '周五'),
        (5, '周六'),
        (6, '周日'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField('星期几', choices=WEEKDAY_CHOICES)
    start_time = models.TimeField('开始时间')
    end_time = models.TimeField('结束时间')
    is_active = models.BooleanField('是否有效', default=True)
    
    class Meta:
        verbose_name = '课程安排'
        verbose_name_plural = '课程安排'
        ordering = ['weekday', 'start_time']
        unique_together = ['course', 'weekday', 'start_time']
    
    def __str__(self):
        return f"{self.course.name} - {self.get_weekday_display()} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
    
    def clean(self):
        """验证结束时间在开始时间之后"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('结束时间必须在开始时间之后')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class SheetMusic(models.Model):
    """曲谱模型"""
    title = models.CharField('曲谱名称', max_length=100)
    composer = models.CharField('作曲家', max_length=100)
    level = models.ForeignKey(PianoLevel, on_delete=models.SET_NULL, null=True, related_name='sheet_music')
    description = models.TextField('描述', blank=True)
    file = models.FileField('曲谱文件', upload_to='sheet_music/')
    cover_image = models.ImageField('封面图片', upload_to='sheet_music/covers/', null=True, blank=True)
    upload_date = models.DateTimeField('上传日期', auto_now_add=True)
    uploaded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='uploaded_sheet_music')
    is_public = models.BooleanField('是否公开', default=True)
    
    # 新增字段用于筛选
    DIFFICULTY_CHOICES = [
        ('入门级', '入门级'),
        ('初级', '初级'),
        ('中级', '中级'),
        ('高级', '高级'),
        ('专业级', '专业级'),
    ]
    
    STYLE_CHOICES = [
        ('古典', '古典'),
        ('浪漫', '浪漫'),
        ('现代', '现代'),
        ('爵士', '爵士'),
        ('流行', '流行'),
    ]
    
    PERIOD_CHOICES = [
        ('巴洛克', '巴洛克'),
        ('古典主义', '古典主义'),
        ('浪漫主义', '浪漫主义'),
        ('现代主义', '现代主义'),
        ('当代', '当代'),
    ]
    
    difficulty = models.CharField('难度级别', max_length=20, choices=DIFFICULTY_CHOICES, default='中级')
    style = models.CharField('曲谱风格', max_length=20, choices=STYLE_CHOICES, default='古典')
    period = models.CharField('时期', max_length=20, choices=PERIOD_CHOICES, default='古典主义')
    
    class Meta:
        verbose_name = '曲谱'
        verbose_name_plural = '曲谱'
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.title} - {self.composer}"


class PracticeSessionScheduler:
    """练习会话调度器（工具类，用于自动排课）"""
    @staticmethod
    def get_available_piano():
        """获取可用的钢琴"""
        return Piano.objects.filter(is_active=True, is_occupied=False).order_by('number').first()
    
    @staticmethod
    def calculate_wait_time(position_in_queue):
        """计算预计等待时间（分钟）"""
        # 假设每个学生练习30分钟
        standard_practice_time = 30
        # 等待时间 = 队列位置 * 标准练习时间
        return position_in_queue * standard_practice_time
    
    @staticmethod
    def get_queue_position(session_id, student_id):
        """获取学生在队列中的位置"""
        from mymanage.attendance.models import WaitingQueue
        student_position = WaitingQueue.objects.filter(
            session_id=session_id,
            is_active=True,
            join_time__lt=WaitingQueue.objects.get(
                session_id=session_id,
                student_id=student_id,
                is_active=True
            ).join_time
        ).count()
        return student_position

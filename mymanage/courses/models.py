from django.db import models
from django.utils import timezone
from mymanage.teachers.models import Teacher
from mymanage.students.models import Student


class Course(models.Model):
    """
    课程信息模型
    """
    COURSE_STATUS_CHOICES = (
        ('active', '进行中'),
        ('completed', '已结束'),
        ('upcoming', '即将开始'),
    )
    
    # 钢琴课等级选项
    LEVEL_CHOICES = (
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
    )
    
    name = models.CharField('课程名称', max_length=100)
    code = models.CharField('课程代码', max_length=20, unique=True)
    level = models.IntegerField('课程等级', choices=LEVEL_CHOICES, default=1)
    description = models.TextField('课程描述', blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='courses')
    max_students = models.IntegerField('最大学生数', default=10)
    start_date = models.DateField('开始日期')
    end_date = models.DateField('结束日期')
    status = models.CharField('状态', max_length=10, choices=COURSE_STATUS_CHOICES, default='upcoming')
    tuition_fee = models.DecimalField('学费', max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '课程'
        verbose_name_plural = '课程'
        ordering = ['start_date']
        
    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"
    
    def get_current_enrollment_count(self):
        """获取当前课程的有效报名人数"""
        return self.enrollments.filter(status='active').count()
    
    def is_full(self):
        """检查课程是否已满"""
        return self.get_current_enrollment_count() >= self.max_students
    
    def get_available_seats(self):
        """获取课程剩余名额"""
        return max(0, self.max_students - self.get_current_enrollment_count())


class CourseSchedule(models.Model):
    """
    课程安排模型，记录每节课的具体时间
    苗韵琴行只有一个教室，所以不需要记录地点
    """
    WEEKDAY_CHOICES = (
        (0, '周一'),
        (1, '周二'),
        (2, '周三'),
        (3, '周四'),
        (4, '周五'),
        (5, '周六'),
        (6, '周日'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField('星期', choices=WEEKDAY_CHOICES)
    start_time = models.TimeField('开始时间')
    end_time = models.TimeField('结束时间')
    
    class Meta:
        verbose_name = '课程安排'
        verbose_name_plural = '课程安排'
        ordering = ['weekday', 'start_time']
        
    def __str__(self):
        return f"{self.course.name} - {self.get_weekday_display()} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
    
    def is_conflicting(self, other_schedule):
        """检查两个课程安排是否冲突"""
        if self.weekday != other_schedule.weekday:
            return False
            
        # 检查时间是否重叠
        if (self.start_time <= other_schedule.end_time and 
            self.end_time >= other_schedule.start_time):
            return True
            
        return False


class Enrollment(models.Model):
    """
    学生课程报名模型
    """
    STATUS_CHOICES = (
        ('active', '在读'),
        ('completed', '已完成'),
        ('dropped', '已退课'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enroll_date = models.DateField('报名日期', auto_now_add=True)
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='active')
    payment_status = models.BooleanField('学费支付状态', default=False)
    
    class Meta:
        verbose_name = '课程报名'
        verbose_name_plural = '课程报名'
        unique_together = ['student', 'course']
        ordering = ['-enroll_date']
        
    def __str__(self):
        return f"{self.student.name} - {self.course.name}"


class Piano(models.Model):
    """
    钢琴信息模型 - 苗韵琴行只有七台钢琴
    """
    PIANO_CHOICES = (
        (1, '钢琴1号'),
        (2, '钢琴2号'),
        (3, '钢琴3号'),
        (4, '钢琴4号'),
        (5, '钢琴5号'),
        (6, '钢琴6号'),
        (7, '钢琴7号'),
    )
    
    piano_number = models.IntegerField('钢琴编号', choices=PIANO_CHOICES, unique=True)
    location = models.CharField('位置', max_length=100, default='苗韵琴行教室')
    is_occupied = models.BooleanField('是否占用', default=False)
    
    class Meta:
        verbose_name = '钢琴'
        verbose_name_plural = '钢琴'
        
    def __str__(self):
        return f"钢琴{self.piano_number}号"
        
    def check_in(self):
        """占用钢琴"""
        if not self.is_occupied:
            self.is_occupied = True
            self.save()
            return True
        return False
    
    def check_out(self):
        """释放钢琴"""
        if self.is_occupied:
            self.is_occupied = False
            self.save()
            return True
        return False


class SheetMusic(models.Model):
    """
    钢琴曲谱模型，用于存储老师上传的曲谱
    """
    LEVEL_CHOICES = (
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
    )
    
    title = models.CharField('曲谱标题', max_length=100)
    composer = models.CharField('作曲家', max_length=100)
    level = models.IntegerField('难度等级', choices=LEVEL_CHOICES)
    description = models.TextField('描述', blank=True)
    sheet_file = models.FileField('曲谱文件', upload_to='sheet_music/')
    uploaded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='uploaded_sheets')
    upload_date = models.DateTimeField('上传时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '钢琴曲谱'
        verbose_name_plural = '钢琴曲谱'
        ordering = ['level', 'title']
        
    def __str__(self):
        return f"{self.title} ({self.get_level_display()}) - {self.composer}"

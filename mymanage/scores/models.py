from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from mymanage.students.models import Student
from mymanage.teachers.models import Teacher
from mymanage.courses.models import Course


class ExamType(models.Model):
    """
    考试类型模型
    """
    name = models.CharField('考试类型名称', max_length=100)
    description = models.TextField('描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '考试类型'
        verbose_name_plural = '考试类型'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Exam(models.Model):
    """
    考试模型
    """
    STATUS_CHOICES = (
        ('pending', '未开始'),
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    
    name = models.CharField('考试名称', max_length=200)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name='exams', verbose_name='考试类型')
    description = models.TextField('考试描述', blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams', verbose_name='课程')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='exams', verbose_name='考官')
    exam_date = models.DateField('考试日期')
    start_time = models.TimeField('开始时间')
    end_time = models.TimeField('结束时间')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    max_score = models.PositiveIntegerField('满分', default=100)
    passing_score = models.PositiveIntegerField('及格分数', default=60)
    location = models.CharField('考试地点', max_length=200, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '考试'
        verbose_name_plural = '考试'
        ordering = ['-exam_date', '-start_time']
    
    def __str__(self):
        return f"{self.name} - {self.exam_date}"
    
    @property
    def is_past(self):
        """判断考试是否已过期"""
        today = timezone.now().date()
        return self.exam_date < today or (self.exam_date == today and timezone.now().time() > self.end_time)
    
    @property
    def student_count(self):
        """获取参加考试的学生数量"""
        return self.scores.count()
    
    @property
    def passed_count(self):
        """获取及格的学生数量"""
        return self.scores.filter(score__gte=self.passing_score).count()
    
    @property
    def pass_rate(self):
        """获取及格率"""
        if self.student_count == 0:
            return 0
        return (self.passed_count / self.student_count) * 100
    
    @property
    def average_score(self):
        """获取平均分"""
        if self.student_count == 0:
            return 0
        return self.scores.aggregate(models.Avg('score'))['score__avg'] or 0


class Score(models.Model):
    """
    学生成绩模型
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='scores', verbose_name='学生')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='scores', verbose_name='考试')
    score = models.DecimalField('分数', max_digits=5, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(100)])
    comment = models.TextField('评语', blank=True)
    is_absent = models.BooleanField('是否缺席', default=False)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_scores', verbose_name='创建人')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '成绩'
        verbose_name_plural = '成绩'
        ordering = ['-exam__exam_date', 'student__name']
        # 确保一个学生在一场考试中只有一条成绩记录
        unique_together = ['student', 'exam']
    
    def __str__(self):
        return f"{self.student.name} - {self.exam.name} - {self.score}"
    
    @property
    def is_passed(self):
        """判断是否及格"""
        return self.score >= self.exam.passing_score


class ScoreDetail(models.Model):
    """
    成绩详情模型，用于记录成绩的各个评分项
    """
    score = models.ForeignKey(Score, on_delete=models.CASCADE, related_name='details', verbose_name='成绩')
    item_name = models.CharField('评分项名称', max_length=100)
    max_point = models.DecimalField('满分', max_digits=5, decimal_places=1, default=10)
    point = models.DecimalField('得分', max_digits=5, decimal_places=1, validators=[MinValueValidator(0)])
    weight = models.DecimalField('权重', max_digits=3, decimal_places=2, default=1.0, 
                                validators=[MinValueValidator(0), MaxValueValidator(1)])
    comment = models.CharField('评语', max_length=200, blank=True)
    
    class Meta:
        verbose_name = '成绩详情'
        verbose_name_plural = '成绩详情'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.score.student.name} - {self.item_name} - {self.point}/{self.max_point}"


class ScoreStatistics(models.Model):
    """
    成绩统计模型，用于记录课程成绩的统计数据
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='score_statistics', verbose_name='课程')
    exam_count = models.PositiveIntegerField('考试次数', default=0)
    student_count = models.PositiveIntegerField('参考学生数', default=0)
    average_score = models.DecimalField('平均分', max_digits=5, decimal_places=1, default=0)
    highest_score = models.DecimalField('最高分', max_digits=5, decimal_places=1, default=0)
    lowest_score = models.DecimalField('最低分', max_digits=5, decimal_places=1, default=0)
    pass_rate = models.DecimalField('及格率', max_digits=5, decimal_places=2, default=0)
    excellent_rate = models.DecimalField('优秀率', max_digits=5, decimal_places=2, default=0)
    statistics_date = models.DateField('统计日期', default=timezone.now)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '成绩统计'
        verbose_name_plural = '成绩统计'
        ordering = ['-statistics_date']
    
    def __str__(self):
        return f"{self.course.name} - {self.statistics_date} 成绩统计"


class PerformanceLevel(models.Model):
    """
    表现等级模型，用于对学生的表现进行等级评定
    """
    name = models.CharField('等级名称', max_length=50)
    min_score = models.DecimalField('最低分数', max_digits=5, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_score = models.DecimalField('最高分数', max_digits=5, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(100)])
    description = models.TextField('描述', blank=True)
    color_code = models.CharField('颜色代码', max_length=20, default='#000000')
    is_active = models.BooleanField('是否启用', default=True)
    
    class Meta:
        verbose_name = '表现等级'
        verbose_name_plural = '表现等级'
        ordering = ['min_score']
    
    def __str__(self):
        return f"{self.name} ({self.min_score}-{self.max_score})"

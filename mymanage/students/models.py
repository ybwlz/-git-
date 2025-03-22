from django.db import models
from mymanage.users.models import User


class Student(models.Model):
    """
    学生信息模型
    """
    GENDER_CHOICES = (
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField('学号', max_length=20, unique=True)
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES, default='other')
    birth_date = models.DateField('出生日期', null=True, blank=True)
    address = models.CharField('地址', max_length=200, blank=True)
    parent_name = models.CharField('家长姓名', max_length=50, blank=True)
    parent_phone = models.CharField('家长电话', max_length=11)
    join_date = models.DateField('入学日期', auto_now_add=True)
    is_active = models.BooleanField('是否活跃', default=True)
    
    class Meta:
        verbose_name = '学生'
        verbose_name_plural = '学生'
        ordering = ['-join_date']
        
    def __str__(self):
        return f"{self.name} ({self.student_id})"


class StudentNotes(models.Model):
    """
    学生笔记和备注模型
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField('标题', max_length=100)
    content = models.TextField('内容')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_notes')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '学生笔记'
        verbose_name_plural = '学生笔记'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.student.name} - {self.title}"

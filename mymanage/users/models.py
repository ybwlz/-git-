from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型"""
    USER_TYPE_CHOICES = (
        ('admin', '管理员'),
        ('teacher', '教师'),
        ('student', '学生'),
    )
    
    user_type = models.CharField('用户类型', max_length=10, choices=USER_TYPE_CHOICES, default='student')
    phone = models.CharField('手机号码', max_length=11, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', null=True, blank=True)
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
    
    @property
    def is_student(self):
        return self.user_type == 'student'
    
    @property
    def is_teacher(self):
        return self.user_type == 'teacher'
        
    @property
    def is_admin_user(self):
        return self.user_type == 'admin'
    
    def __str__(self):
        return self.username

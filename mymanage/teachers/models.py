from django.db import models
from mymanage.users.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class TeacherProfile(models.Model):
    """教师个人信息模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=[('男', '男'), ('女', '女')])
    phone = models.CharField('手机号码', max_length=11)
    avatar = models.ImageField('头像', upload_to='teachers/avatars/', null=True, blank=True)
    bio = models.TextField('个人简介', blank=True)
    specialties = models.JSONField('教学专长', default=list)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '教师'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

# 添加信号处理器，自动为新教师创建默认课程
@receiver(post_save, sender=TeacherProfile)
def create_default_course_for_teacher(sender, instance, created, **kwargs):
    """当新教师被创建时，关联到系统默认课程"""
    if created:  # 只在教师首次创建时执行
        from mymanage.courses.models import Course, PianoLevel
        # 获取或创建默认钢琴等级
        piano_level, _ = PianoLevel.objects.get_or_create(
            level=1,
            defaults={'description': '初级'}
        )
        
        # 尝试获取已存在的默认课程
        default_course = Course.objects.filter(code='DEFAULT').first()
        
        if not default_course:
            # 如果没有默认课程，创建一个新的
            default_course = Course.objects.create(
                name='通用考勤',
                code='DEFAULT',
                teacher=instance,  # 第一个创建的教师将成为默认课程的教师
                description='系统通用考勤课程',
                level=piano_level
            )
            print(f"创建了系统默认课程，教师为 {instance.name}")
        else:
            # 如果已经存在默认课程，将新教师添加为该课程的教师
            default_course.teacher = instance
            default_course.save()
            print(f"教师 {instance.name} 已关联到系统默认课程")


class PrivacySetting(models.Model):
    """教师隐私设置模型"""
    teacher = models.OneToOneField(TeacherProfile, on_delete=models.CASCADE, related_name='privacy_setting')
    phone_visibility = models.CharField('手机号可见性', max_length=10, 
        choices=[('self', '仅自己可见'), ('students', '仅学生可见'), ('all', '所有人可见')],
        default='self')
    email_visibility = models.CharField('邮箱可见性', max_length=10,
        choices=[('self', '仅自己可见'), ('students', '仅学生可见'), ('all', '所有人可见')],
        default='self')
    bio_visibility = models.CharField('简介可见性', max_length=10,
        choices=[('self', '仅自己可见'), ('students', '仅学生可见'), ('all', '所有人可见')],
        default='all')

    class Meta:
        verbose_name = '隐私设置'
        verbose_name_plural = verbose_name

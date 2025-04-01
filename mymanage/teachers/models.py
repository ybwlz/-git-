from django.db import models
from mymanage.users.models import User

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
        verbose_name = '教师信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class TeacherCertificate(models.Model):
    """教师证书模型"""
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField('证书名称', max_length=100)
    issue_date = models.DateField('发证日期')
    expire_date = models.DateField('有效期至', null=True, blank=True)
    issuing_authority = models.CharField('发证机构', max_length=100)
    certificate_no = models.CharField('证书编号', max_length=50, blank=True)
    image = models.ImageField('证书图片', upload_to='teachers/certificates/')
    is_verified = models.BooleanField('已验证', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '教师证书'
        verbose_name_plural = verbose_name
        
    def __str__(self):
        return f"{self.teacher.name} - {self.title}"

class NotificationSetting(models.Model):
    """教师通知设置模型"""
    teacher = models.OneToOneField(TeacherProfile, on_delete=models.CASCADE, related_name='notification_setting')
    course_reminder = models.BooleanField('课程提醒', default=True)
    attendance_reminder = models.BooleanField('考勤提醒', default=True)
    fee_reminder = models.BooleanField('学费提醒', default=True)
    in_app = models.BooleanField('站内消息', default=True)
    sms = models.BooleanField('短信通知', default=False)
    email = models.BooleanField('邮件通知', default=False)

    class Meta:
        verbose_name = '通知设置'
        verbose_name_plural = verbose_name

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

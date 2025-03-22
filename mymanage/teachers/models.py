from django.db import models
from mymanage.users.models import User


class Teacher(models.Model):
    """
    教师信息模型
    """
    GENDER_CHOICES = (
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField('教师工号', max_length=20, unique=True)
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES, default='other')
    birth_date = models.DateField('出生日期', null=True, blank=True)
    phone = models.CharField('电话', max_length=11)
    address = models.CharField('地址', max_length=200, blank=True)
    email = models.EmailField('邮箱', blank=True)
    specialty = models.CharField('专业特长', max_length=100, blank=True)
    join_date = models.DateField('入职日期', auto_now_add=True)
    is_active = models.BooleanField('是否在职', default=True)
    
    class Meta:
        verbose_name = '教师'
        verbose_name_plural = '教师'
        ordering = ['-join_date']
        
    def __str__(self):
        return f"{self.name} ({self.specialty})"


class TeacherCertificate(models.Model):
    """
    教师证书模型
    """
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='certificates')
    certificate_name = models.CharField('证书名称', max_length=100)
    certificate_number = models.CharField('证书编号', max_length=50, blank=True)
    issue_date = models.DateField('颁发日期')
    issue_organization = models.CharField('颁发机构', max_length=100)
    certificate_image = models.ImageField('证书图片', upload_to='certificates/', blank=True, null=True)
    
    class Meta:
        verbose_name = '教师证书'
        verbose_name_plural = '教师证书'
        ordering = ['-issue_date']
        
    def __str__(self):
        return f"{self.teacher.name} - {self.certificate_name}"

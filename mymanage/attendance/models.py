from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
# 使用字符串引用模型，避免循环导入
# from mymanage.students.models import Student
# from mymanage.courses.models import Course, CourseSchedule, Piano
from mymanage.users.models import User


class QRCode(models.Model):
    """
    二维码模型，用于生成和存储课程考勤的二维码
    """
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='qrcodes')
    uuid = models.UUIDField('唯一标识', default=uuid.uuid4, editable=False)
    # 添加code字段以保持兼容性
    code = models.CharField('二维码字符串', max_length=100, blank=True, null=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    expires_at = models.DateTimeField('过期时间')
    qr_code_image = models.ImageField('二维码图片', upload_to='qrcodes/', blank=True, null=True)
    
    class Meta:
        verbose_name = '二维码'
        verbose_name_plural = '二维码'
        ordering = ['-created_at']
    
    def __str__(self):
        # 确保created_at不为None
        if self.created_at:
            time_str = self.created_at.strftime('%Y-%m-%d %H:%M')
        else:
            time_str = timezone.now().strftime('%Y-%m-%d %H:%M')
        return f"二维码-{self.course.name}-{time_str}"
    
    def save(self, *args, **kwargs):
        # 设置code字段与uuid一致
        if not self.code:
            self.code = str(self.uuid)
            
        # 生成二维码图片
        if not self.qr_code_image:
            qr = qrcode.QRCode(
                version=4,  # 更高的版本支持更多数据
                error_correction=qrcode.constants.ERROR_CORRECT_M,  # 提高纠错级别
                box_size=10,
                border=4,
            )
            
            # 使用更明确的数据格式，确保包含UUID和其他信息
            qr_data = str(self.uuid)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 使用BytesIO作为临时文件
            buffer = BytesIO()
            # 保存为高质量图片
            img.save(buffer, format="PNG", quality=95)
            
            # 使用当前时间代替self.created_at，因为created_at可能为None
            current_time = timezone.now()
            filename = f"{self.course.code}_{current_time.strftime('%Y%m%d%H%M')}.png"
            
            self.qr_code_image.save(
                filename,
                File(buffer),
                save=False
            )
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """检查二维码是否有效（未过期）"""
        return timezone.now() < self.expires_at


class AttendanceSession(models.Model):
    """
    考勤会话模型，代表一次课程的考勤记录集合
    """
    STATUS_CHOICES = (
        ('active', '进行中'),
        ('closed', '已关闭'),
    )
    
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='attendance_sessions', null=True, blank=True)
    schedule = models.ForeignKey('courses.CourseSchedule', on_delete=models.CASCADE, related_name='attendance_sessions', null=True, blank=True)
    qrcode = models.OneToOneField(QRCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='session')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sessions')
    start_time = models.DateTimeField('开始时间', auto_now_add=True)
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='active')
    description = models.TextField('描述', blank=True)
    is_active = models.BooleanField('是否活跃', default=True)
    
    class Meta:
        verbose_name = '考勤会话'
        verbose_name_plural = '考勤会话'
        ordering = ['-start_time']
    
    def __str__(self):
        course_name = self.course.name if self.course else "未关联课程"
        return f"{course_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def attendance_count(self):
        """获取考勤人数"""
        return self.records.count()
    
    @property
    def total_students(self):
        """获取总学生数"""
        if self.course:
            return self.course.students.count()
        return 0
    
    def clean(self):
        """验证数据的有效性"""
        # 如果是新创建的会话，不做时间验证
        if not self.pk:
            return
            
        # 只对已存在的会话进行时间验证
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError({
                'end_time': '结束时间必须在开始时间之后'
            })
    
    def save(self, *args, **kwargs):
        """重写save方法，确保结束时间晚于开始时间"""
        # 如果是新创建的会话，直接保存
        if not self.pk:
            super().save(*args, **kwargs)
            return
            
        # 对已存在的会话执行验证
        self.clean()
        super().save(*args, **kwargs)
    
    def close_session(self):
        """关闭考勤会话"""
        self.status = 'closed'
        self.is_active = False
        self.end_time = timezone.now()
        self.save()
        
        # 释放所有钢琴
        for record in self.records.filter(status='checked_in'):
            record.check_out()
    
    @classmethod
    def check_and_close_expired_sessions(cls):
        """检查并关闭所有过期的考勤会话"""
        current_time = timezone.now()
        # 获取所有活跃状态但已过期的会话
        expired_sessions = cls.objects.filter(
            is_active=True,
            end_time__lt=current_time
        )
        
        count = 0
        for session in expired_sessions:
            session.close_session()
            count += 1
        
        return count


class AttendanceRecord(models.Model):
    """
    考勤记录模型，记录学生的签到和签退信息
    """
    STATUS_CHOICES = (
        ('checked_in', '已签到'),
        ('checked_out', '已签退'),
    )
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_records')
    piano = models.ForeignKey('courses.Piano', on_delete=models.SET_NULL, null=True, related_name='attendance_records')
    check_in_time = models.DateTimeField('签到时间', auto_now_add=True)
    check_out_time = models.DateTimeField('签退时间', null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='checked_in')
    duration = models.FloatField('学习时长(小时)', null=True, blank=True)
    duration_minutes = models.FloatField('学习时长(分钟)', null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    note = models.TextField('签到备注', blank=True)
    check_in_method = models.CharField('签到方式', max_length=20, default='qrcode', blank=True)
    
    class Meta:
        verbose_name = '考勤记录'
        verbose_name_plural = '考勤记录'
        ordering = ['-check_in_time']
        unique_together = ['session', 'student']
    
    def __str__(self):
        return f"{self.student.name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"
    
    def check_out(self):
        """学生签退"""
        if self.status == 'checked_in':
            self.check_out_time = timezone.now()
            self.status = 'checked_out'
            # 计算学习时长
            self.duration = (self.check_out_time - self.check_in_time).total_seconds() / 3600
            self.duration_minutes = self.duration * 60
            # 释放钢琴
            if self.piano:
                self.piano.is_occupied = False
                self.piano.save()
            self.save()
            
            # 从等待队列中分配下一个学生
            next_in_queue = WaitingQueue.objects.filter(
                session=self.session,
                is_active=True
            ).order_by('join_time').first()
            
            if next_in_queue and self.piano:
                # 自动分配钢琴给下一个学生
                self.piano.is_occupied = True
                self.piano.save()
                
                # 创建新的考勤记录
                AttendanceRecord.objects.create(
                    session=self.session,
                    student=next_in_queue.student,
                    piano=self.piano
                )
                
                # 从等待队列中移除学生
                next_in_queue.is_active = False
                next_in_queue.save()
                
            return True
        return False


class WaitingQueue(models.Model):
    """
    等待队列模型，管理学生等待分配钢琴的队列
    """
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='waiting_queue')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='waiting_records')
    join_time = models.DateTimeField('加入时间', auto_now_add=True)
    estimated_wait_time = models.IntegerField('预计等待时间(分钟)', default=0)
    is_active = models.BooleanField('是否在队列中', default=True)
    
    class Meta:
        verbose_name = '等待队列'
        verbose_name_plural = '等待队列'
        ordering = ['join_time']
    
    def __str__(self):
        return f"{self.student.name} - {self.join_time.strftime('%Y-%m-%d %H:%M')}"

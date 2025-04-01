from django.db import models
from django.utils import timezone
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
        return f"二维码-{self.course.name}-{self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # 设置code字段与uuid一致
        if not self.code:
            self.code = str(self.uuid)
            
        # 生成二维码图片
        if not self.qr_code_image:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(str(self.uuid))
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            
            self.qr_code_image.save(
                f"{self.course.code}_{self.created_at.strftime('%Y%m%d%H%M')}.png",
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
    
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='attendance_sessions')
    schedule = models.ForeignKey('courses.CourseSchedule', on_delete=models.CASCADE, related_name='attendance_sessions')
    qrcode = models.OneToOneField(QRCode, on_delete=models.SET_NULL, null=True, related_name='session')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sessions')
    start_time = models.DateTimeField('开始时间', auto_now_add=True)
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = '考勤会话'
        verbose_name_plural = '考勤会话'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.course.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def close_session(self):
        """关闭考勤会话"""
        self.status = 'closed'
        self.end_time = timezone.now()
        self.save()
        
        # 释放所有钢琴
        for record in self.records.filter(status='checked_in'):
            record.check_out()


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
    duration = models.DurationField('学习时长', null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    
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
            self.duration = self.check_out_time - self.check_in_time
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

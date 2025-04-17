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
import logging


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
        # 获取日志记录器
        logger = logging.getLogger(__name__)
        
        # 记录调试信息
        logger.debug(f"关闭会话: ID={self.id}, 开始时间={self.start_time}, 状态={self.status}")
        
        # 获取当前本地时间
        current_time = timezone.localtime(timezone.now())
        
        # 检查并修复可能的时间异常
        if self.start_time and self.start_time > current_time:
            logger.warning(f"会话{self.id}的开始时间{self.start_time}晚于当前时间{current_time}，自动修正")
            # 设置开始时间为当前时间前1小时
            self.start_time = current_time - timezone.timedelta(hours=1)
        
        # 如果有关联的二维码，更新二维码的过期时间为当前时间，使其立即过期
        if hasattr(self, 'qrcode') and self.qrcode:
            logger.debug(f"更新二维码过期时间: ID={self.qrcode.id}, 原过期时间={self.qrcode.expires_at}")
            self.qrcode.expires_at = current_time
            self.qrcode.save()
            logger.debug(f"二维码已更新为过期: ID={self.qrcode.id}, 新过期时间={current_time}")
        
        # 更新状态和结束时间
        self.status = 'closed'
        self.is_active = False
        self.end_time = current_time
        
        try:
            # 尝试保存
            self.save()
        except ValidationError as e:
            logger.error(f"关闭会话时验证错误: {e}")
            # 使用底层save方法绕过验证
            from django.db import models
            models.Model.save(self)
            logger.info(f"已使用绕过验证的方式关闭会话{self.id}")
        
        # 释放所有钢琴
        for record in self.records.filter(status='checked_in'):
            try:
                record.check_out()
            except Exception as e:
                logger.error(f"释放钢琴失败: {e}")
                # 直接更新记录状态
                record.status = 'checked_out'
                record.check_out_time = current_time
                record.save()
    
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
    duration = models.DecimalField('学习时长(小时)', max_digits=4, decimal_places=1, null=True, blank=True)
    duration_minutes = models.DecimalField('学习时长(分钟)', max_digits=5, decimal_places=1, null=True, blank=True)
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
    
    def save(self, *args, **kwargs):
        """重写保存方法，添加时区检查"""
        from django.utils import timezone
        import logging
        logger = logging.getLogger(__name__)
        
        # 检查签到时间是否有时区信息
        if self.check_in_time and timezone.is_naive(self.check_in_time):
            logger.warning(f"签到时间没有时区信息: {self.check_in_time}")
            self.check_in_time = timezone.make_aware(self.check_in_time)
        
        # 检查签退时间是否有时区信息
        if self.check_out_time and timezone.is_naive(self.check_out_time):
            logger.warning(f"签退时间没有时区信息: {self.check_out_time}")
            self.check_out_time = timezone.make_aware(self.check_out_time)
        
        # 如果有签到和签退时间，重新计算持续时间
        if self.check_in_time and self.check_out_time:
            # 确保两个时间都是aware的
            duration = (self.check_out_time - self.check_in_time).total_seconds()
            if duration < 0:
                logger.error(f"时间计算异常: 签退时间早于签到时间 - 签到: {self.check_in_time}, 签退: {self.check_out_time}")
                # 使用默认30分钟
                duration = 1800
            self.duration = duration / 3600  # 转换为小时
            self.duration_minutes = duration / 60  # 转换为分钟
        
        super().save(*args, **kwargs)
    
    def check_out(self):
        """签退方法，更新签退时间和状态"""
        if self.status == 'checked_in':  # 只有处于签到状态才能签退
            
            import logging
            logger = logging.getLogger(__name__)
            
            from django.utils import timezone
            current_time = timezone.now()
            
            self.check_out_time = current_time
            self.status = 'checked_out'
            
            # 计算持续时间（小时）
            check_in_local = self.check_in_time
            if check_in_local:
                if check_in_local > current_time:
                    # 时间异常，可能是时区问题
                    logger.warning(f"签到时间异常: {check_in_local} > {current_time}")
                    from datetime import timedelta
                    # 使用默认持续时间30分钟
                    self.duration = 0.5
                    self.duration_minutes = 30
                else:
                    # 正常计算持续时间
                    # 重新计算持续时间
                    duration = (current_time - check_in_local).total_seconds() / 3600
                    self.duration = duration
                    self.duration_minutes = duration * 60
            
            # 释放钢琴
            if self.piano:
                logger.info(f"正在释放钢琴: 编号={self.piano.number}")
                
                # 检查是否有其他学生正在使用此钢琴
                other_records = AttendanceRecord.objects.filter(
                    piano=self.piano,
                    status='checked_in'
                ).exclude(id=self.id).exists()
                
                # 检查是否有关联的PracticeRecord
                from mymanage.students.models import PracticeRecord
                practice_records = PracticeRecord.objects.filter(
                    student=self.student,
                    status='active',
                    piano_number=self.piano.number
                )
                
                # 更新所有相关的PracticeRecord
                for practice in practice_records:
                    practice.status = 'completed'
                    practice.end_time = current_time
                    # 计算时长(分钟)
                    if practice.start_time:
                        duration_mins = (current_time - practice.start_time).total_seconds() / 60
                        practice.duration = int(duration_mins)
                    practice.save()
                    logger.info(f"已更新关联的PracticeRecord: ID={practice.id}, 学生={practice.student.name}")
                
                if not other_records:
                    # 没有其他记录使用此钢琴，可以释放
                    self.piano.stop_using()
                    logger.info(f"钢琴已释放: 编号={self.piano.number}")
                    
                    # 尝试将钢琴分配给等待队列中的下一个学生
                    from mymanage.attendance.models import PianoAssignment
                    assignment = PianoAssignment.assign_piano_to_next_waiting_student(self.session)
                    if assignment:
                        logger.info(f"钢琴已分配给等待队列中的下一个学生: {assignment.student.name}")
                else:
                    logger.info(f"钢琴仍有其他学生使用，保持占用状态: 编号={self.piano.number}")
            
            self.save()
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
    practice_record = models.ForeignKey('students.PracticeRecord', 
                                      on_delete=models.SET_NULL, 
                                      null=True, 
                                      blank=True, 
                                      related_name='waiting_queue_record',
                                      verbose_name='关联练琴记录')
    
    class Meta:
        verbose_name = '等待队列'
        verbose_name_plural = '等待队列'
        ordering = ['join_time']
    
    def __str__(self):
        return f"{self.student.name} - {self.join_time.strftime('%Y-%m-%d %H:%M')}"


class PianoAssignment(models.Model):
    """
    钢琴分配模型，记录学生扫码后的钢琴预留和分配情况
    """
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='piano_assignments')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='piano_assignments')
    piano = models.ForeignKey('courses.Piano', on_delete=models.CASCADE, related_name='assignments')
    reserved_time = models.DateTimeField('预留时间', auto_now_add=True)
    expiration_time = models.DateTimeField('预留过期时间')
    status = models.CharField('状态', max_length=20, choices=[
        ('reserved', '已预留'),
        ('assigned', '已分配'),
        ('expired', '已过期'),
        ('cancelled', '已取消')
    ], default='reserved')
    
    class Meta:
        verbose_name = '钢琴分配'
        verbose_name_plural = '钢琴分配'
        ordering = ['reserved_time']
    
    def __str__(self):
        return f"钢琴{self.piano.number}分配 - {self.student.name} - {self.reserved_time.strftime('%Y-%m-%d %H:%M')}"
    
    def is_expired(self):
        """检查预留是否已过期"""
        return timezone.now() > self.expiration_time
    
    def expire(self):
        """将预留标记为已过期"""
        if self.status == 'reserved':
            self.status = 'expired'
            self.save()
            # 释放钢琴预留
            self.piano.cancel_reservation()
            return True
        return False
    
    def assign(self):
        """将预留转为正式分配"""
        if self.status == 'reserved' and not self.is_expired():
            self.status = 'assigned'
            self.save()
            # 更新钢琴状态为占用
            self.piano.start_using()
            return True
        return False
    
    def cancel(self):
        """取消预留"""
        if self.status == 'reserved':
            self.status = 'cancelled'
            self.save()
            # 释放钢琴预留
            self.piano.cancel_reservation()
            return True
        return False
    
    @classmethod
    def check_and_expire_reservations(cls):
        """检查并过期所有已超时的预留"""
        expired_reservations = cls.objects.filter(
            status='reserved',
            expiration_time__lt=timezone.now()
        )
        
        for reservation in expired_reservations:
            reservation.expire()
        
        # 同时检查钢琴自身的预留状态
        from mymanage.courses.models import Piano
        Piano.check_and_expire_reservations()
    
    @classmethod
    def assign_piano_to_next_waiting_student(cls, session):
        """将钢琴分配给等待队列中的下一个学生"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 获取可用钢琴
        from mymanage.courses.models import Piano
        available_pianos = Piano.objects.filter(
            is_active=True,
            is_occupied=False,
            is_reserved=False
        ).order_by('number')
        
        if not available_pianos.exists():
            logger.info("没有可用钢琴，无法分配")
            return None
        
        # 获取等待队列中的第一个学生
        next_in_queue = WaitingQueue.objects.filter(
            session=session,
            is_active=True
        ).order_by('join_time').first()
        
        if not next_in_queue:
            logger.info("等待队列为空，无需分配")
            return None
        
        piano = available_pianos.first()
        student = next_in_queue.student
        
        # 为学生预留钢琴（30秒内有效）
        reservation_time = 0.5  # 30秒
        piano.reserve_for_student(student, minutes=reservation_time)
        
        # 创建预留记录
        expiration_time = timezone.now() + timezone.timedelta(minutes=reservation_time)
        assignment = cls.objects.create(
            session=session,
            student=student,
            piano=piano,
            expiration_time=expiration_time,
            status='reserved'
        )
        
        # 更新等待队列记录状态
        next_in_queue.is_active = False
        next_in_queue.save()
        
        logger.info(f"为等待学生 {student.name} 分配钢琴 {piano.number}，预留时间 {reservation_time} 分钟")
        
        return assignment

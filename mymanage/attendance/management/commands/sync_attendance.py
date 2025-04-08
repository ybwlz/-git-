from django.core.management.base import BaseCommand
from django.utils import timezone
from mymanage.attendance.models import AttendanceRecord
from mymanage.students.models import PracticeRecord, Student

class Command(BaseCommand):
    help = '同步考勤记录(AttendanceRecord)和练琴记录(PracticeRecord)，确保数据一致性'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student',
            help='指定学生姓名进行同步，不指定则同步所有学生'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行'
        )

    def handle(self, *args, **options):
        student_name = options.get('student')
        dry_run = options.get('dry_run')
        
        if student_name:
            try:
                students = Student.objects.filter(name=student_name)
                if not students.exists():
                    self.stdout.write(self.style.ERROR(f'找不到学生: {student_name}'))
                    return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'查询学生出错: {str(e)}'))
                return
        else:
            students = Student.objects.all()
        
        self.stdout.write(self.style.SUCCESS(f'开始同步{student_name if student_name else "所有学生"}的考勤和练琴记录...'))
        
        total_synced = 0
        
        for student in students:
            self.stdout.write(f'处理学生: {student.name}')
            
            # 获取学生的所有考勤记录
            attendance_records = AttendanceRecord.objects.filter(
                student=student,
                status='checked_out'  # 只处理已签退的记录
            )
            
            for record in attendance_records:
                # 检查是否已有对应的练琴记录
                existing_record = PracticeRecord.objects.filter(
                    student=student,
                    date=record.check_in_time.date(),
                    start_time=record.check_in_time
                ).first()
                
                if not existing_record:
                    # 确定持续时间
                    duration = None
                    if hasattr(record, 'duration_minutes') and record.duration_minutes is not None:
                        duration_value = record.duration_minutes
                        if duration_value < 0 or duration_value > 240:
                            # 限制为最大4小时（240分钟）或最小0分钟
                            duration = 240 if duration_value > 0 else 0
                        else:
                            duration = int(duration_value)
                    else:
                        # 如果没有时长，但有签退时间，计算时长
                        if record.check_out_time:
                            duration_seconds = (record.check_out_time - record.check_in_time).total_seconds()
                            duration = int(duration_seconds / 60)
                            if duration < 0 or duration > 240:
                                duration = 240 if duration > 0 else 0
                        else:
                            duration = 240  # 默认4小时
                    
                    # 确保钢琴编号有效
                    piano_number = 1  # 默认钢琴编号
                    if record.piano and hasattr(record.piano, 'number'):
                        piano_number = record.piano.number
                    
                    # 创建新的练琴记录
                    if not dry_run:
                        try:
                            PracticeRecord.objects.create(
                                student=student,
                                date=record.check_in_time.date(),
                                start_time=record.check_in_time,
                                end_time=record.check_out_time,
                                duration=duration,
                                piano_number=piano_number,
                                status='completed',
                                attendance_session=record.session
                            )
                            total_synced += 1
                            self.stdout.write(self.style.SUCCESS(
                                f'  创建练琴记录: {student.name}, 日期={record.check_in_time.date()}, '
                                f'时长={duration}分钟'
                            ))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  创建练琴记录失败: {str(e)}'))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'  [DRY RUN] 将创建练琴记录: {student.name}, 日期={record.check_in_time.date()}, '
                            f'时长={duration}分钟'
                        ))
                        total_synced += 1
                else:
                    self.stdout.write(f'  已存在练琴记录，跳过: {student.name}, ID={existing_record.id}')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'DRY RUN完成，将同步{total_synced}条记录'))
        else:
            self.stdout.write(self.style.SUCCESS(f'同步完成，共同步{total_synced}条记录')) 
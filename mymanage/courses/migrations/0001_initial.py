# Generated by Django 4.2.7 on 2025-03-23 09:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('teachers', '0001_initial'),
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='课程名称')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='课程代码')),
                ('level', models.IntegerField(choices=[(1, '1级'), (2, '2级'), (3, '3级'), (4, '4级'), (5, '5级'), (6, '6级'), (7, '7级'), (8, '8级'), (9, '9级'), (10, '10级')], default=1, verbose_name='课程等级')),
                ('description', models.TextField(blank=True, verbose_name='课程描述')),
                ('max_students', models.IntegerField(default=10, verbose_name='最大学生数')),
                ('start_date', models.DateField(verbose_name='开始日期')),
                ('end_date', models.DateField(verbose_name='结束日期')),
                ('status', models.CharField(choices=[('active', '进行中'), ('completed', '已结束'), ('upcoming', '即将开始')], default='upcoming', max_length=10, verbose_name='状态')),
                ('tuition_fee', models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name='学费')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='teachers.teacher')),
            ],
            options={
                'verbose_name': '课程',
                'verbose_name_plural': '课程',
                'ordering': ['start_date'],
            },
        ),
        migrations.CreateModel(
            name='Piano',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('piano_number', models.IntegerField(choices=[(1, '钢琴1号'), (2, '钢琴2号'), (3, '钢琴3号'), (4, '钢琴4号'), (5, '钢琴5号'), (6, '钢琴6号'), (7, '钢琴7号')], unique=True, verbose_name='钢琴编号')),
                ('location', models.CharField(default='苗韵琴行教室', max_length=100, verbose_name='位置')),
                ('is_occupied', models.BooleanField(default=False, verbose_name='是否占用')),
            ],
            options={
                'verbose_name': '钢琴',
                'verbose_name_plural': '钢琴',
            },
        ),
        migrations.CreateModel(
            name='SheetMusic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='曲谱标题')),
                ('composer', models.CharField(max_length=100, verbose_name='作曲家')),
                ('level', models.IntegerField(choices=[(1, '1级'), (2, '2级'), (3, '3级'), (4, '4级'), (5, '5级'), (6, '6级'), (7, '7级'), (8, '8级'), (9, '9级'), (10, '10级')], verbose_name='难度等级')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('sheet_file', models.FileField(upload_to='sheet_music/', verbose_name='曲谱文件')),
                ('upload_date', models.DateTimeField(auto_now_add=True, verbose_name='上传时间')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_sheets', to='teachers.teacher')),
            ],
            options={
                'verbose_name': '钢琴曲谱',
                'verbose_name_plural': '钢琴曲谱',
                'ordering': ['level', 'title'],
            },
        ),
        migrations.CreateModel(
            name='CourseSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.IntegerField(choices=[(0, '周一'), (1, '周二'), (2, '周三'), (3, '周四'), (4, '周五'), (5, '周六'), (6, '周日')], verbose_name='星期')),
                ('start_time', models.TimeField(verbose_name='开始时间')),
                ('end_time', models.TimeField(verbose_name='结束时间')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='courses.course')),
            ],
            options={
                'verbose_name': '课程安排',
                'verbose_name_plural': '课程安排',
                'ordering': ['weekday', 'start_time'],
            },
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enroll_date', models.DateField(auto_now_add=True, verbose_name='报名日期')),
                ('status', models.CharField(choices=[('active', '在读'), ('completed', '已完成'), ('dropped', '已退课')], default='active', max_length=10, verbose_name='状态')),
                ('payment_status', models.BooleanField(default=False, verbose_name='学费支付状态')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='courses.course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='students.student')),
            ],
            options={
                'verbose_name': '课程报名',
                'verbose_name_plural': '课程报名',
                'ordering': ['-enroll_date'],
                'unique_together': {('student', 'course')},
            },
        ),
    ]

# Generated by Django 4.2.7 on 2025-04-02 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_attendancesession_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='check_in_method',
            field=models.CharField(blank=True, default='qrcode', max_length=20, verbose_name='签到方式'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='duration_minutes',
            field=models.FloatField(blank=True, null=True, verbose_name='学习时长(分钟)'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='note',
            field=models.TextField(blank=True, verbose_name='签到备注'),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='duration',
            field=models.FloatField(blank=True, null=True, verbose_name='学习时长(小时)'),
        ),
    ]

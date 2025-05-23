# Generated by Django 4.2.7 on 2025-04-07 15:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_alter_attendance_options_and_more'),
        ('courses', '0004_alter_courseschedule_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='piano',
            name='is_reserved',
            field=models.BooleanField(default=False, verbose_name='是否被预留'),
        ),
        migrations.AddField(
            model_name='piano',
            name='reserved_for',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reserved_pianos', to='students.student'),
        ),
        migrations.AddField(
            model_name='piano',
            name='reserved_until',
            field=models.DateTimeField(blank=True, null=True, verbose_name='预留结束时间'),
        ),
    ]

# Generated by Django 5.1.6 on 2025-03-04 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='registration',
            options={},
        ),
        migrations.AlterUniqueTogether(
            name='formresponse',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='registration',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='formresponse',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='form_responses/'),
        ),
        migrations.AlterField(
            model_name='formresponse',
            name='value',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='registration',
            name='qr_code',
            field=models.ImageField(blank=True, null=True, upload_to='qrcodes/'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
        migrations.RemoveField(
            model_name='registration',
            name='check_in_by',
        ),
        migrations.RemoveField(
            model_name='registration',
            name='check_in_time',
        ),
        migrations.RemoveField(
            model_name='registration',
            name='email',
        ),
        migrations.RemoveField(
            model_name='registration',
            name='full_name',
        ),
    ]

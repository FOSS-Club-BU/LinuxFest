# Generated by Django 5.1.6 on 2025-03-16 14:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0008_alter_formresponse_value_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='emailcommunication',
            unique_together=set(),
        ),
    ]

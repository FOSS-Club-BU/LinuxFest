from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from events.models import Event, FormField
from django.contrib.auth.models import User
import uuid

class Registration(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('checked_in', 'Checked In'),
        ('not_attending', 'Not Attending'),
        ('declined', 'Declined'),
    )

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    registration_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    check_in_time = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_in_registrations')

    class Meta:
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.name} - {self.event.name} ({self.status})"

class FormResponse(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='form_responses')
    field = models.ForeignKey(FormField, on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='form_responses/', blank=True, null=True)

    def __str__(self):
        return f"{self.registration.name} - {self.field.label}: {self.value}"

class EmailCommunication(models.Model):
    EMAIL_TYPE_CHOICES = (
        ('registration_approved', 'Registration Approved'),
        ('registration_rejected', 'Registration Rejected'),
        ('event_update', 'Event Update'),
    )

    id = models.AutoField(primary_key=True)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='email_communications', null=True, blank=True)
    email_type = models.CharField(max_length=50, choices=EMAIL_TYPE_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.registration.name} - {self.email_type} ({self.timestamp})"

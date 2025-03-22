import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from .models import Registration, EmailCommunication
import io
from ics import Calendar, Event as IcsEvent
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def send_bulk_emails(request):
    """
    Send emails to all approved participants with custom content, iCal, and QR code attachments.
    """
    if not request.user.is_superuser:
        return HttpResponse("You are not authorized to perform this action.", status=403)

    if request.method == 'POST':
        approved_registrations = Registration.objects.filter(status='approved')
        for registration in approved_registrations:
            # Check if email has already been sent
            if EmailCommunication.objects.filter(registration=registration, email_type='event_update').exists():
                print(f"Email already sent to {registration.email}")
                continue
            print(f"Sending email to {registration.email}")

            # Generate iCal Event
            calendar = Calendar()
            event = IcsEvent()
            event.name = registration.event.name
            # event.begin = registration.event.start_time
            # event model has a date field and a time field
            event.begin = datetime.datetime(2025, 3, 23, 10, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))

            # event.end = registration.event.end_time
            # event ends after 4 hours of starting
            event.end = event.begin + datetime.timedelta(hours=4)
            event.description = registration.event.description
            calendar.events.add(event)
            ical_io = io.StringIO(str(calendar))
            ical_io.seek(0)

            # Format custom content
            # email_body = custom_content.format(name=registration.name, event_name=registration.event.name, registration=registration)
            email_body = render_to_string('emails/registration_custom.html', {
                'name': registration.name,
                'event_name': registration.event.name,
                'registration': registration,
            })

            # Send Email
            email = EmailMessage(
                subject=f"[Reminder] Linux Fest 2025",
                body=email_body,
                to=[registration.email],
                reply_to=['foss@bennett.edu.in'],
            )
            email.content_subtype = "html"  # Set email content type to HTML
            email.attach('event.ics', ical_io.read(), 'text/calendar')
            email.send()

            # Create EmailCommunication object
            print(f"Email sent to {registration.email}")
            EmailCommunication.objects.create(
                registration=registration,
                email_type='event_update'
            )

        return HttpResponse("Emails sent successfully.")
    return render(request, 'registrations/send_bulk_emails.html')

def decline_success(request, registration_uuid):
    """
    Display the success page after declining an RSVP.
    """
    registration = get_object_or_404(Registration, uuid=registration_uuid)
    return render(request, 'registrations/decline_success.html', {
        'registration': registration,
        'event': registration.event,
    })

def rsvp_decline(request, registration_uuid):
    """
    Handle RSVP decline for a registration with confirmation.
    """
    registration = get_object_or_404(Registration, uuid=registration_uuid)

    if request.method == 'POST':
        if registration.status != 'approved':
            return JsonResponse({'error': 'Only approved registrations can RSVP.'}, status=400)
        
        # Update the status to 'declined'
        registration.status = 'declined'
        registration.save()
        
        messages.success(request, 'Your RSVP has been updated. We are sorry to hear you won’t be attending.')
        return redirect('registrations:decline_success', registration_uuid=registration.uuid)

    return render(request, 'registrations/decline.html', {
        'registration': registration,
        'event': registration.event,
    })

def confirmation(request, registration_id):
    """
    Display the confirmation page for a registration and check email status.
    """
    registration = get_object_or_404(Registration, id=registration_id)
    return render(request, 'registrations/confirmation.html', {
        'registration': registration,
        'event': registration.event,
    })

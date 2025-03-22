from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import json
import csv
from events.models import Event, FormField
from registrations.models import Registration, EmailCommunication

def is_staff_check(user):
    return user.is_superuser

@user_passes_test(is_staff_check)
def export_registrations(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registrations = Registration.objects.filter(event=event).select_related('event')
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{event.name.replace(" ", "_")}_registrations.csv"'
    
    writer = csv.writer(response)
    
    # Get all form fields for this event
    form_fields = event.form_fields.all().order_by('order')
    
    # Write header row
    header = [
        'Registration ID', 
        'UUID',
        'Status', 
        'Name', 
        'Email',
        'Registration Date',
        'Check-in Time',
        'Checked-in By'
    ]
    # Add form field labels to header
    header.extend([field.label for field in form_fields])
    writer.writerow(header)
    
    # Write data rows
    for registration in registrations:
        # Get all form responses for this registration
        responses = {
            response.field_id: response.value or response.file.url if response.file else response.value
            for response in registration.form_responses.all()
        }
        
        row = [
            registration.id,
            registration.uuid,
            registration.status,
            registration.name,
            registration.email,
            registration.registration_date.strftime('%Y-%m-%d %H:%M:%S'),
            registration.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if registration.check_in_time else 'Not checked in',
            registration.checked_in_by.get_full_name() if registration.checked_in_by else 'N/A'
        ]
        
        # Add form responses in correct order
        for field in form_fields:
            row.append(responses.get(field.id, ''))
        
        writer.writerow(row)
    
    return response

@user_passes_test(is_staff_check)
def dashboard_home(request):
    events = Event.objects.all().order_by('-date')[:5]
    registrations = Registration.objects.select_related('event').order_by('-registration_date')[:10]
    pending_registrations = Registration.objects.filter(status='pending').count()

    return render(request, 'dashboard/index.html', {
        'events': events,
        'registrations': registrations,
        'pending_registrations': pending_registrations,
    })

@user_passes_test(is_staff_check)
def event_list(request):
    events = Event.objects.all().order_by('-date')
    return render(request, 'dashboard/events/list.html', {'events': events})

@user_passes_test(is_staff_check)
def event_registrations(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registrations = Registration.objects.filter(event=event).order_by('-registration_date')
    stats = {
        'total': registrations.count(),
        'pending': registrations.filter(status='pending').count(),
        'approved': registrations.filter(status='approved').count(),
        'rejected': registrations.filter(status='rejected').count(),
    }
    return render(request, 'dashboard/events/registrations.html', {
        'event': event,
        'registrations': registrations,
        'stats': stats,
    })

@user_passes_test(is_staff_check)
def event_create(request):
    if request.method == 'POST':
        try:
            event = Event.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                date=request.POST.get('date'),
                time=request.POST.get('time'),
                location=request.POST.get('location'),
                max_attendees=request.POST.get('max_attendees'),
                registration_open=request.POST.get('registration_open') == 'on'
            )
            messages.success(request, 'Event created successfully')
            return redirect('dashboard:event_list')
        except Exception as e:
            messages.error(request, f'Error creating event: {str(e)}')
    return render(request, 'dashboard/events/create.html')

@user_passes_test(is_staff_check)
def event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        try:
            event.name = request.POST.get('name')
            event.description = request.POST.get('description')
            event.date = request.POST.get('date')
            event.time = request.POST.get('time')
            event.location = request.POST.get('location')
            event.max_attendees = request.POST.get('max_attendees')
            event.registration_open = request.POST.get('registration_open') == 'on'
            event.save()
            messages.success(request, 'Event updated successfully')
            return redirect('dashboard:event_list')
        except Exception as e:
            messages.error(request, f'Error updating event: {str(e)}')
    return render(request, 'dashboard/events/edit.html', {'event': event})

@user_passes_test(is_staff_check)
def form_builder(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    fields = event.form_fields.all().order_by('order')
    return render(request, 'dashboard/events/form_builder.html', {
        'event': event,
        'fields': fields,
    })

@user_passes_test(is_staff_check)
def form_field_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        try:
            conditional_field_id = request.POST.get('conditional_field')
            conditional_field = None
            if conditional_field_id:
                conditional_field = FormField.objects.get(id=conditional_field_id)

            field = FormField.objects.create(
                event=event,
                label=request.POST.get('label'),
                field_type=request.POST.get('field_type'),
                required=request.POST.get('required') == 'on',
                placeholder=request.POST.get('placeholder', ''),
                choices=request.POST.get('choices', ''),
                order=FormField.objects.filter(event=event).count(),
                conditional_field=conditional_field,
                conditional_value=request.POST.get('conditional_value', '')
            )
            messages.success(request, 'Form field added successfully')
            return redirect('dashboard:form_builder', event_id=event.id)
        except Exception as e:
            messages.error(request, f'Error creating form field: {str(e)}')
    return render(request, 'dashboard/fields/create.html', {
        'event': event,
        'field_types': FormField.FIELD_TYPES,
        'existing_fields': event.form_fields.all()
    })

@user_passes_test(is_staff_check)
def form_field_edit(request, field_id):
    field = get_object_or_404(FormField, id=field_id)
    if request.method == 'POST':
        try:
            conditional_field_id = request.POST.get('conditional_field')
            conditional_field = None
            if conditional_field_id:
                conditional_field = FormField.objects.get(id=conditional_field_id)
            
            field.label = request.POST.get('label')
            field.field_type = request.POST.get('field_type')
            field.required = request.POST.get('required') == 'on'
            field.placeholder = request.POST.get('placeholder', '')
            field.choices = request.POST.get('choices', '')
            field.conditional_field = conditional_field
            field.conditional_value = request.POST.get('conditional_value', '')
            field.save()
            messages.success(request, 'Form field updated successfully')
            return redirect('dashboard:form_builder', event_id=field.event.id)
        except Exception as e:
            messages.error(request, f'Error updating form field: {str(e)}')
    return render(request, 'dashboard/fields/edit.html', {
        'field': field,
        'field_types': FormField.FIELD_TYPES,
        'existing_fields': field.event.form_fields.exclude(id=field.id)
    })

@user_passes_test(is_staff_check)
def form_field_delete(request, field_id):
    field = get_object_or_404(FormField, id=field_id)
    event_id = field.event.id
    if request.method == 'POST':
        field.delete()
        messages.success(request, 'Form field deleted successfully')
    return redirect('dashboard:form_builder', event_id=event_id)

@require_POST
@user_passes_test(is_staff_check)
def reorder_fields(request, event_id):
    try:
        data = json.loads(request.body)
        for idx, field_id in enumerate(data.get('order', [])):
            FormField.objects.filter(id=field_id).update(order=idx)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@user_passes_test(is_staff_check)
def registration_list(request):
    registrations = Registration.objects.all().select_related('event').order_by('-registration_date')
    return render(request, 'dashboard/registrations/list.html', {
        'registrations': registrations
    })

@user_passes_test(is_staff_check)
def registration_detail(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    responses = registration.form_responses.select_related('field')
    emails = EmailCommunication.objects.filter(registration=registration)
    print(emails)
    return render(request, 'dashboard/registrations/detail.html', {
        'emails': emails,
        'registration': registration,
        'responses': responses,
    })

@user_passes_test(is_staff_check)
def approve_registration(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    if request.method == 'POST':
        registration.status = 'approved'
        registration.save()
        messages.success(request, 'Registration approved successfully')
        return redirect('dashboard:registration_detail', registration_id=registration.id)

@user_passes_test(is_staff_check)
def reject_registration(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    if request.method == 'POST':
        registration.status = 'rejected'
        registration.save()
        messages.success(request, 'Registration rejected successfully')
        return redirect('dashboard:registration_detail', registration_id=registration.id)

@user_passes_test(is_staff_check)
def send_approval_email(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id, status='approved')
    
    context = {
        'registration': registration,
        'event': registration.event
    }
    
    email_body = render_to_string('emails/registration_approved.html', context)

    email_message = EmailMessage(
        subject=f"Your Registration for {registration.event.name} is Approved!",
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[registration.email],
        reply_to=["foss@bennett.edu.in"]
    )
    
    email_message.content_subtype = "html"
    email_message.send()

    EmailCommunication.objects.create(
        registration=registration,
        email_type='registration_approved'
    )



    # send_mail(
    #     subject=f"Your Registration for {registration.event.name} is Approved!",
    #     message=email_body,
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     reply_to="foss@bennett.edu.in",
    #     recipient_list=[registration.email],
    #     html_message=email_body
    # )
    
    messages.success(request, f"Approval email with QR code sent to {registration.email}")
    return redirect('dashboard:registration_detail', registration_id=registration.id)

@user_passes_test(is_staff_check)
def send_rejection_email(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id, status='rejected')
    
    context = {
        'registration': registration,
        'event': registration.event,
    }
    
    email_body = render_to_string('emails/registration_rejected.html', context)
    
    send_mail(
        subject=f"Registration Update for {registration.event.name}",
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        reply_to="foss@bennett.edu.in",
        recipient_list=[registration.email],
        html_message=email_body
    )
    
    messages.success(request, f"Rejection email sent to {registration.email}")
    return redirect('dashboard:registration_detail', registration_id=registration.id)

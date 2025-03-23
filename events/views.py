from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import qrcode
from io import BytesIO
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Event, FormField
from registrations.models import Registration, FormResponse
from .forms import DynamicRegistrationForm
import json

def event_list(request):
    events = Event.objects.filter(registration_open=True).order_by('date', 'time')
    return render(request, 'events/event_list.html', {
        'events': events
    })

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if not event.registration_open:
        return render(request, 'events/registration_closed.html', {
            'event': event
        })
    
    form = DynamicRegistrationForm(event=event)
    return render(request, 'events/event_detail.html', {
        'event': event,
        'form': form
    })

def event_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if not event.registration_open:
        return render(request, 'events/registration_closed.html', {
            'event': event
        })
    
    if request.method == 'POST':
        form = DynamicRegistrationForm(request.POST, request.FILES, event=event)
        try:
            with transaction.atomic():
                # Get all form fields for this event
                event_fields = {
                    f'field_{field.id}': field 
                    for field in event.form_fields.all()
                }
                
                # Get name and email directly from form data
                name = None
                email = None
                for field_name, value in request.POST.items():
                    if field_name in event_fields:
                        field = event_fields[field_name]
                        if field.label.lower() == "full name":
                            name = value
                        elif field.label.lower() == "email":
                            email = value

                if email:
                    existing_registration = Registration.objects.filter(email=email, event=event).first()
                    if existing_registration:
                        raise ValidationError('A registration already exists with this email address.')

                # Create registration
                registration = Registration.objects.create(
                    event=event,
                    status='pending',
                    name=name or "Unknown",
                    email=email or "unknown@example.com"
                )
                
                # Process form fields
                for field_name, value in request.POST.items():
                    if field_name in event_fields:
                        field = event_fields[field_name]
                        
                        # Skip fields that should be hidden based on conditions
                        if form._should_field_be_hidden(field_name, request.POST):
                            continue
                        
                        # Handle file uploads separately
                        if field.field_type == 'file' and field_name in request.FILES:
                            FormResponse.objects.create(
                                registration=registration,
                                field=field,
                                file=request.FILES[field_name]
                            )
                        elif value:  # Only save non-empty values
                            FormResponse.objects.create(
                                registration=registration,
                                field=field,
                                value=str(value)
                            )
                
                messages.success(request, 'Application submitted successfully!')
                return redirect('registrations:confirmation', registration_id=registration.id)
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'An error occurred during registration. Please try again.')
            print(e)
    else:
        form = DynamicRegistrationForm(event=event)
    
    return render(request, 'events/event_detail.html', {
        'event': event,
        'form': form
    })

def get_conditional_fields(request):
    """AJAX endpoint to get conditional fields based on a field's value"""
    if request.method == 'GET':
        field_id = request.GET.get('field_id')
        value = request.GET.get('value')
        
        if not field_id or not value:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
            
        try:
            dependent_fields = FormField.objects.filter(
                conditional_field_id=field_id,
                conditional_value=value
            ).order_by('order')
            
            fields_data = [{
                'id': field.id,
                'label': field.label,
                'type': field.field_type,
                'required': field.required,
                'placeholder': field.placeholder,
                'choices': field.get_choices() if field.field_type == 'choice' else None
            } for field in dependent_fields]
            
            return JsonResponse({'fields': fields_data})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def generate_qr(request, data):
    """Generate and render a QR code for the given data."""
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    import base64
    qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
    return render(request, 'events/qr_code.html', {'qr_code_url': qr_code_url})
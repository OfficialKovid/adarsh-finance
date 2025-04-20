from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from apps.loan.models import LoanScheme, LoanApplication
from .models import FormSubmission
import os
import json

@login_required
def fill_form(request, scheme_slug):
    # Get the scheme
    scheme = get_object_or_404(LoanScheme, slug=scheme_slug, is_active=True)
    
    # Check if user has an active application for this scheme
    existing_application = LoanApplication.objects.filter(
        user=request.user,
        scheme=scheme,
        status__in=['new_lead', 'assigned', 'detail_collection', 'form_filled', 'under_review']
    ).first()
    
    if not existing_application:
        messages.error(request, "You haven't applied for this loan scheme yet.")
        return redirect('list_loans')
    
    # Check if form is already submitted
    existing_submission = FormSubmission.objects.filter(
        application=existing_application
    ).first()
    
    if existing_submission:
        return render(request, 'customer/form_already_submitted.html', {
            'submission': existing_submission,
            'scheme': scheme
        })
    
    # Get form fields
    form_fields = scheme.required_data_fields.all().order_by('display_order')
    
    context = {
        'scheme': scheme,
        'form_fields': form_fields,
        'application': existing_application
    }
    
    return render(request, 'customer/fill_form.html', context)

@login_required
def submit_form(request, scheme_slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Get the scheme
    scheme = get_object_or_404(LoanScheme, slug=scheme_slug, is_active=True)

    try:
        # Get existing application for this user and scheme
        application = LoanApplication.objects.filter(
            user=request.user,
            scheme=scheme,
            status__in=['new_lead', 'assigned', 'detail_collection']
        ).first()

        if not application:
            return JsonResponse({
                'status': 'error',
                'message': "No active application found for this loan scheme"
            })

        # Process form data
        form_data = {}
        file_data = {}
        
        # Get scheme's required fields
        required_fields = scheme.required_data_fields.all()
        
        # Process each field
        for field in required_fields:
            if field.field_type == 'file':
                if field.field_name in request.FILES:
                    file = request.FILES[field.field_name]
                    file_path = f'form_submissions/{application.reference_number}/{field.field_name}/{file.name}'
                    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Save file
                    with open(full_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                            
                    file_data[field.field_name] = file_path
            else:
                form_data[field.field_name] = request.POST.get(field.field_name)
        
        # Create or update form submission
        FormSubmission.objects.update_or_create(
            application=application,
            defaults={
                'scheme': scheme,
                'submitted_by': request.user,
                'data': form_data,
                'files': file_data
            }
        )
        
        # Update application status
        application.status = 'form_filled'
        application.save()
        
        return JsonResponse({
            'status': 'success',
            'redirect_url': '/applications/success/'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

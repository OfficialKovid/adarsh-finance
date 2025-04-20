from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib import messages
from .models import LoanScheme, Benefit, EligibilityCriteria, RequiredDocument, CoveredSector, KeyPoint, LoanApplication, RequiredDataField
from django.contrib.auth import get_user_model
from django.db.models import Q, Value
from django.db.models.functions import Concat
import json, logging
from apps.documents.models import RequiredDocument, DocumentType  # Add this import

logger = logging.getLogger(__name__)

def list_loans(request):
    loans = LoanScheme.objects.filter(is_active=True).prefetch_related(
        'key_points',
        'covered_sectors'
    )
    return render(request, 'loan/list_loans.html', {'loans': loans})

def is_manager_user(user):
    return user.role == 'MANAGER'  # Use the role field from MyUser model

@login_required(login_url='dashboard/staff-login/')
@user_passes_test(is_manager_user, login_url='dashboard/staff-login/')
def add_new_loan(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validate that at least one item exists in each section
                sections = {
                    'benefits[]': 'benefits',
                    'criteria[]': 'eligibility criteria',
                    'documents[]': 'required documents',
                    'data_field_names[]': 'data fields',
                    'sectors[]': 'sectors'
                }

                for field, name in sections.items():
                    values = [v.strip() for v in request.POST.getlist(field) if v.strip()]
                    if not values:
                        messages.error(request, f'Please add or select at least one {name}')
                        return redirect('add_new_loan')

                # Create new loan scheme
                scheme = LoanScheme.objects.create(
                    title=request.POST['title'],
                    full_name=request.POST['full_name'],  # changed from short_name
                    description=request.POST['description'],
                    start_year=request.POST.get('start_year') or None,  # handle optional field
                    end_year=request.POST.get('end_year') or None,      # handle optional field
                    contact_info=request.POST['contact_info'],
                    image=request.FILES.get('image')
                )

                # Add sectors
                sectors = request.POST.get('sectors[]', '').split(',')
                for sector in sectors:
                    if sector:
                        CoveredSector.objects.create(
                            scheme=scheme,
                            sector_name=sector
                        )

                # Add benefits
                benefits = request.POST.getlist('benefits[]')
                for benefit in benefits:
                    if benefit:
                        Benefit.objects.create(scheme=scheme, description=benefit)

                # Add eligibility criteria
                criteria_list = request.POST.getlist('criteria[]')
                for criteria in criteria_list:
                    if criteria:
                        EligibilityCriteria.objects.create(scheme=scheme, criteria=criteria)

                # Update document creation
                documents = request.POST.getlist('documents[]')
                document_types = request.POST.getlist('document_types[]')
                
                for i, doc in enumerate(documents):
                    if doc:
                        doc_type_id = document_types[i] if i < len(document_types) else 1  # Default to first type (PDF)
                        RequiredDocument.objects.create(
                            scheme=scheme,
                            document_name=doc,
                            document_type_id=doc_type_id
                        )

                # Add key points
                key_points = request.POST.getlist('key_points[]')
                for i, point in enumerate(key_points[:3]):  # Limit to 3 points
                    if point:
                        KeyPoint.objects.create(
                            scheme=scheme,
                            point=point,
                            display_order=i
                        )

                # Add required data fields
                field_names = request.POST.getlist('data_field_names[]')
                field_types = request.POST.getlist('data_field_types[]')
                field_required = request.POST.getlist('data_field_required[]')
                field_options = request.POST.getlist('data_field_options[]')

                for i, (name, type_) in enumerate(zip(field_names, field_types)):
                    if name and type_:
                        is_required = 'on' in (field_required[i] if i < len(field_required) else 'on')
                        options = field_options[i] if i < len(field_options) else None
                        
                        if type_ in ['select', 'radio', 'checkbox'] and not options:
                            options = ''  # Ensure options is not None for these field types
                            
                        RequiredDataField.objects.create(
                            scheme=scheme,
                            field_name=name,
                            field_type=type_,
                            is_required=is_required,
                            display_order=i,
                            options=options
                        )

                messages.success(request, 'Loan scheme created successfully')
                return redirect('list_loans')
                
        except Exception as e:
            messages.error(request, f'Error creating loan scheme: {str(e)}')
            return redirect('add_new_loan')

    # Fetch all existing items
    context = {
        'existing_sectors': CoveredSector.objects.values_list('sector_name', flat=True).distinct().order_by('sector_name'),
        'existing_benefits': Benefit.objects.values_list('description', flat=True).distinct().order_by('description'),
        'existing_criteria': EligibilityCriteria.objects.values_list('criteria', flat=True).distinct().order_by('criteria'),
        'existing_documents': RequiredDocument.objects.values_list('document_name', flat=True).distinct().order_by('document_name'),
        'existing_key_points': KeyPoint.objects.values_list('point', flat=True).distinct().order_by('point'),
        'existing_data_fields': RequiredDataField.objects.values('field_name', 'field_type').distinct().order_by('field_name'),
        'document_types': DocumentType.objects.filter(is_active=True).order_by('name'),  # Add this line
    }
    return render(request, 'loan/add_new_loan.html', context)

def loan_details(request, slug):
    loan = get_object_or_404(LoanScheme, slug=slug, is_active=True)
    context = {
        'loan': loan,
        'benefits': loan.benefits.all(),
        'criteria': loan.eligibility_criteria.all(),
        'documents': loan.required_documents.all(),
        'sectors': loan.covered_sectors.all(),
        'key_points': loan.key_points.all()[:3],
        'can_fill_form': request.user.is_authenticated
    }
    return render(request, 'loan/loan_details.html', context)

@require_POST
def apply_loan(request, slug):
    try:
        loan = get_object_or_404(LoanScheme, slug=slug)
        application = LoanApplication.objects.create(
            name=request.POST['name'],
            phone_number=request.POST['phone_number'],
            scheme=loan,
            status='new_lead',
            user=request.user if request.user.is_authenticated else None
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required(login_url='/dashboard/staff-login/')
@user_passes_test(is_manager_user, login_url='/dashboard/staff-login/')
def applications_list(request):
    # Get base queryset
    base_applications = LoanApplication.objects.select_related('scheme', 'assigned_agent')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '').strip()
    section = request.GET.get('section', 'all-applications')
    status = request.GET.get('status')
    scheme = request.GET.get('scheme')
    agent = request.GET.get('agent')
    
    # Apply search if provided
    if search_query:
        base_applications = base_applications.filter(
            Q(name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(scheme__title__icontains=search_query) |
            Q(assigned_agent__first_name__icontains=search_query) |
            Q(assigned_agent__last_name__icontains=search_query)
        )
    
    # First, apply section-specific filtering
    if section == 'new-leads':
        applications = base_applications.filter(status='new_lead')
    elif section == 'processing':
        applications = base_applications.filter(status__in=['assigned', 'detail_collection', 'form_filled', 'under_review'])
    elif section == 'completed':
        applications = base_applications.filter(status='closed')
    elif section == 'rejected':
        applications = base_applications.filter(status='Rejected')  # Changed this line
    else:  # all-applications
        applications = base_applications.all()

    # Then apply additional filters
    if status:
        applications = applications.filter(status=status)
    if scheme:
        applications = applications.filter(scheme_id=scheme)
    if agent:
        applications = applications.filter(assigned_agent_id=agent)
        
    # Get all agents
    agents = get_user_model().objects.filter(role='AGENT')
    
    # Prepare unfiltered counts for each section
    unfiltered_applications = LoanApplication.objects.all()
    
    context = {
        'applications': applications,
        'all_applications': unfiltered_applications.count(),
        'new_leads': unfiltered_applications.filter(status='new_lead').count(),
        'processing': unfiltered_applications.filter(
            status__in=['assigned', 'detail_collection', 'form_filled', 'under_review']
        ).count(),
        'completed': unfiltered_applications.filter(status='closed').count(),
        'rejected': unfiltered_applications.filter(status='Rejected').count(),  # Changed this line
        'schemes': LoanScheme.objects.all(),
        'agents': agents,
        'status_choices': LoanApplication.get_status_choices(),
        'current_section': section,
        'current_status': status,
        'current_scheme': scheme,
        'current_agent': agent,
    }
    
    context.update({
        'search_query': search_query,
        'search_count': applications.count() if search_query else None
    })
    
    return render(request, 'loan/applications_list.html', context)

@login_required(login_url='/dashboard/staff-login/')
@user_passes_test(is_manager_user, login_url='/dashboard/staff-login/')
@require_POST
def update_application_status(request, application_id):
    try:
        application = LoanApplication.objects.get(id=application_id)
        new_status = request.POST.get('status')
        
        if not new_status:
            return JsonResponse({
                'status': 'error',
                'message': 'Status is required'
            })
            
        # Update status
        application.status = new_status
        application.save()
        
        # If status is changed to not_converted or closed, remove agent assignment
        if new_status in ['not_converted', 'closed']:
            application.assigned_agent = None
            application.save()
        
        return JsonResponse({
            'status': 'success',
            'new_status': application.status
        })
    except LoanApplication.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Application not found'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required(login_url='/dashboard/staff-login/')
@user_passes_test(is_manager_user, login_url='/dashboard/staff-login/')
@require_POST
@transaction.atomic
def assign_agent(request, application_id):
    try:
        application = LoanApplication.objects.select_for_update().get(id=application_id)
        agent_id = request.POST.get('agent_id')
        
        if not agent_id or agent_id == 'null':
            # Remove agent assignment
            application.assigned_agent = None
            application.status = 'new_lead'
            application.save(update_fields=['assigned_agent', 'status'])
            return JsonResponse({
                'status': 'success',
                'new_status': 'new_lead',
                'message': 'Agent assignment removed'
            })

        try:
            agent = get_user_model().objects.get(id=agent_id, role='AGENT', is_active=True)
        except get_user_model().DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Selected agent does not exist or is not active'
            })

        # Update application with agent and status
        application.assigned_agent = agent
        if application.status == 'new_lead':
            application.status = 'assigned'
            
        application.save(update_fields=['assigned_agent', 'status'])

        return JsonResponse({
            'status': 'success',
            'agent_id': agent.id,
            'new_status': application.status,
            'message': f'Application assigned to {agent.get_full_name()}'
        })

    except LoanApplication.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Application not found'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@user_passes_test(is_manager_user)
def get_search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if query:
        # Get suggestions from different fields
        applications = LoanApplication.objects.annotate(
            full_name=Concat('name', Value(' - '), 'phone_number')
        ).filter(
            Q(name__icontains=query) |
            Q(phone_number__icontains= query) |
            Q(reference_number__icontains=query) |
            Q(scheme__title__icontains=query)
        ).distinct()[:5]  # Limit to 5 suggestions
        
        for app in applications:
            suggestions.append({
                'id': app.id,
                'text': f"{app.name} - {app.phone_number}",
                'reference': app.reference_number,
                'type': 'application'
            })
            
    return JsonResponse({'suggestions': suggestions})

@login_required(login_url='/dashboard/staff-login/')
@user_passes_test(is_manager_user, login_url='/dashboard/staff-login/')
def manage_schemes(request):
    loans = LoanScheme.objects.all().prefetch_related(
        'applications',
        'key_points'
    ).order_by('-created_at')
    
    return render(request, 'loan/manage_schemes.html', {
        'loans': loans
    })

@login_required
@user_passes_test(is_manager_user)
@require_POST
def toggle_scheme_status(request, scheme_id):
    try:
        scheme = get_object_or_404(LoanScheme, id=scheme_id)
        scheme.is_active = not scheme.is_active
        scheme.save()
        return JsonResponse({
            'status': 'success',
            'is_active': scheme.is_active,
            'message': f'Scheme {scheme.title} {"activated" if scheme.is_active else "deactivated"} successfully'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

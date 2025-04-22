from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from apps.accounts.views import agent_required, manager_required
from django.contrib.auth import get_user_model
from apps.loan.models import LoanApplication
from apps.customer.models import FormSubmission  # Updated this import
from apps.documents.models import DocumentUpload  # Add this import
from django.db.models import Count, Avg, Case, When, FloatField, Q
from django.views.decorators.csrf import ensure_csrf_cookie
import logging
from django.contrib.auth.hashers import make_password
from apps.loan.utils import encrypt_password, decrypt_password

logger = logging.getLogger(__name__)

def dashboard(request):
    if request.user.is_authenticated:
        if request.user.role == 'AGENT':
            return agent_dashboard(request)
        elif request.user.role == 'MANAGER':
            return manager_dashboard(request)
    return redirect('staff-login')

@login_required(login_url='/dashboard/staff-login/')
@agent_required
def agent_dashboard(request):
    context = {
        'title': 'Agent Dashboard',
        'role': 'Agent',
        'name': request.user.get_full_name() or request.user.email,
    }
    return render(request, "dashboard/agent/agent_dashboard.html", context)

@login_required(login_url='/dashboard/staff-login/')
@manager_required
def manager_dashboard(request):
    context = {
        'title': 'Manager Dashboard',
        'role': 'Manager',
        'name': request.user.get_full_name() or request.user.email,
    }
    return render(request, "dashboard/manager_dashboard.html", context)

@login_required(login_url='/dashboard/staff-login/')
@manager_required
def agents_management(request):
    User = get_user_model()
    
    # Get all agents
    agents = User.objects.filter(role='AGENT').annotate(
        total_applications=Count('assigned_applications'),
        success_rate=Avg(
            Case(
                When(assigned_applications__status='closed', then=100),
                default=0,
                output_field=FloatField(),
            )
        )
    )
    
    # Calculate statistics
    total_applications = LoanApplication.objects.count()
    active_agents = agents.filter(is_active=True).count()
    
    # Calculate overall success rate
    closed_applications = LoanApplication.objects.filter(status='closed').count()
    success_rate = round((closed_applications / total_applications * 100) if total_applications > 0 else 0)
    
    context = {
        'agents': agents,
        'active_agents': active_agents,
        'total_applications': total_applications,
        'success_rate': success_rate,
    }
    
    return render(request, 'dashboard/agents.html', context)

@login_required(login_url='/dashboard/staff-login/')
@manager_required
def toggle_agent_status(request, agent_id):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=405)
    
    User = get_user_model()
    try:
        agent = User.objects.select_for_update().get(id=agent_id, role='AGENT')
        agent.is_active = not agent.is_active
        agent.save(update_fields=['is_active'])
        
        return JsonResponse({
            'status': 'success',
            'is_active': agent.is_active,
            'message': 'Agent status updated successfully'
        }, status=200)
        
    except User.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Agent not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required(login_url='/dashboard/staff-login/')
@manager_required
@ensure_csrf_cookie
def add_agent(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=405)

    try:
        data = request.POST
        required_fields = ['email', 'password', 'first_name', 'last_name', 'phone_number']
        
        # Check if all required fields are present
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return JsonResponse({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        User = get_user_model()
        
        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Email already exists'
            }, status=400)
        
        # Create new agent
        agent = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone_number'],
            role='AGENT',
            is_active=True
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Agent created successfully',
            'agent': {
                'id': agent.id,
                'name': agent.get_full_name(),
                'email': agent.email,
                'phone_number': agent.phone_number
            }
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required(login_url='/dashboard/staff-login/')
@agent_required
def assigned_applications(request):
    # Get applications assigned to the current agent
    applications = LoanApplication.objects.filter(assigned_agent=request.user)
    
    # Get status choices directly from the model field
    status_choices = [
        {'value': status[0], 'label': status[1]} 
        for status in LoanApplication._meta.get_field('status').choices 
        if status[0] in ['assigned', 'detail_collection', 'form_filled', 'under_review', 'closed', 'dropped']
    ]
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        applications = applications.filter(
            Q(name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(scheme__title__icontains=search_query)
        )
        search_count = applications.count()
    else:
        search_count = None

    # Get counts for different statuses
    status_counts = {
        'all_applications': applications.count(),
        'new_leads': applications.filter(status='new_lead').count(),
        'processing': applications.filter(status__in=['assigned', 'detail_collection', 'form_filled', 'under_review']).count(),
        'completed': applications.filter(status='closed').count(),
        'rejected': applications.filter(status__in=['dropped', 'not_converted']).count(),
    }

    context = {
        'applications': applications,
        'search_query': search_query,
        'search_count': search_count,
        'status_choices': status_choices,  # Add status choices to context
        **status_counts,
    }
    
    return render(request, 'dashboard/agent/assigned_application.html', context)

@login_required(login_url='/dashboard/staff-login/')
@agent_required
def see_application_details(request, application_id):
    logger.debug(f'Accessing application details for ID: {application_id}')
    
    try:
        # Get application and related form submission
        application = get_object_or_404(
            LoanApplication.objects.select_related('scheme', 'user'),
            id=application_id,
            assigned_agent=request.user
        )
        
        # Get form submission data
        form_submission = FormSubmission.objects.filter(application=application).first()
        
        # Get required fields
        form_fields = application.scheme.required_data_fields.all().order_by('display_order')
        
        # Get uploaded documents
        uploaded_documents = DocumentUpload.objects.filter(
            application=application
        ).select_related('required_document')
        
        # Decrypt password for display
        decrypted_password = decrypt_password(application.loan_password) if application.loan_password else None
        
        context = {
            'application': application,
            'form_data': form_submission.data if form_submission else None,
            'files': form_submission.files if form_submission else None,
            'form_fields': form_fields,
            'uploaded_documents': uploaded_documents,
            'decrypted_password': decrypted_password
        }
        
        return render(request, 'dashboard/agent/see_application_details.html', context)
        
    except Exception as e:
        logger.error(f'Error in see_application_details: {str(e)}')
        raise

@login_required
@agent_required
def update_application_credentials(request, application_id):
    if request.method == 'POST':
        application = get_object_or_404(LoanApplication, 
            id=application_id, 
            assigned_agent=request.user
        )
        
        application.loan_application_number = request.POST.get('loan_application_number')
        application.loan_username = request.POST.get('loan_username')
        
        # Encrypt password before saving
        password = request.POST.get('loan_password')
        if password:
            application.loan_password = encrypt_password(password)
        
        if 'report' in request.FILES:
            application.report = request.FILES['report']
        
        application.save()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})
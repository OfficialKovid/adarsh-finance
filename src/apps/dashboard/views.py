from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from apps.accounts.views import agent_required, manager_required
from django.contrib.auth import get_user_model
from apps.loan.models import LoanApplication
from apps.customer.models import FormSubmission
from apps.documents.models import DocumentUpload
from django.db.models import Count, Avg, Case, When, FloatField, Q, F, ExpressionWrapper
from django.views.decorators.csrf import ensure_csrf_cookie
import logging
from django.contrib.auth.hashers import make_password
from apps.loan.utils import encrypt_password, decrypt_password
from django.views.decorators.http import require_POST

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
    # Get agent's applications
    agent_applications = LoanApplication.objects.filter(assigned_agent=request.user)
    
    # Calculate statistics
    total_applications = agent_applications.count()
    pending_review = agent_applications.filter(status='under_review').count()
    approved = agent_applications.filter(status='closed').count()
    
    # Calculate success rate
    success_rate = round((approved / total_applications * 100) if total_applications > 0 else 0)
    
    # Get recent applications
    recent_applications = agent_applications.select_related('scheme').order_by('-applied_at')[:5]
    
    # Get recent documents
    recent_documents = DocumentUpload.objects.filter(
        application__assigned_agent=request.user
    ).select_related(
        'application', 
        'required_document'
    ).order_by('-uploaded_at')[:5]
    
    context = {
        'title': 'Agent Dashboard',
        'role': 'Agent',
        'name': request.user.get_full_name() or request.user.email,
        'total_applications': total_applications,
        'pending_review': pending_review,
        'approved': approved,
        'success_rate': success_rate,
        'recent_applications': recent_applications,
        'recent_documents': recent_documents,
    }
    return render(request, "dashboard/agent/agent_dashboard.html", context)

@login_required(login_url='/dashboard/staff-login/')
@manager_required
def manager_dashboard(request):
    # Get total applications count
    total_applications = LoanApplication.objects.count()

    # Get active agents count
    User = get_user_model()
    active_agents = User.objects.filter(role='AGENT', is_active=True).count()

    # Get pending approvals (applications under review)
    pending_approvals = LoanApplication.objects.filter(status='under_review').count()

    # Get recent activity
    recent_activities = LoanApplication.objects.select_related('assigned_agent').order_by('-applied_at')[:5]

    # Get top performing agents
    top_agents = User.objects.filter(role='AGENT').annotate(
        applications_count=Count('assigned_applications'),
        approved_count=Count('assigned_applications', 
            filter=Q(assigned_applications__status='closed')
        )
    ).filter(applications_count__gt=0).annotate(
        approval_rate=ExpressionWrapper(
            F('approved_count') * 100.0 / F('applications_count'),
            output_field=FloatField()
        )
    ).order_by('-approval_rate')[:3]

    context = {
        'title': 'Manager Dashboard',
        'role': 'Manager',
        'name': request.user.get_full_name() or request.user.email,
        'total_applications': total_applications,
        'active_agents': active_agents,
        'pending_approvals': pending_approvals,
        'recent_activities': recent_activities,
        'top_agents': top_agents,
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
        
        # Update credentials
        application.loan_application_number = request.POST.get('loan_application_number')
        application.loan_username = request.POST.get('loan_username')
        
        # Encrypt password before saving
        password = request.POST.get('loan_password')
        if password:
            application.set_password(password)
        
        # Save report if uploaded
        if 'report' in request.FILES:
            application.report = request.FILES['report']
        
        # Update status to under_review if all required fields are filled
        if all([
            application.loan_application_number,
            application.loan_username,
            application.loan_password,
            application.report
        ]):
            application.status = 'under_review'
        
        application.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Credentials updated successfully',
            'new_status': application.status
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})

@login_required
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
            
        # Update status while keeping assigned agent
        application.status = new_status
        application.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Application status updated successfully',
            'new_status': application.get_status_display()
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

from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(lambda u: u.role == 'MANAGER')
def application_details_admin(request, application_id):
    application = get_object_or_404(LoanApplication, id=application_id)
    
    # Get form submission if exists
    form_submission = FormSubmission.objects.filter(application=application).first()
    
    context = {
        'application': application,
        'form_fields': application.scheme.required_data_fields.all().order_by('display_order'),
        'form_data': form_submission.data if form_submission else None,
        'files': form_submission.files if form_submission else None,
        'uploaded_documents': DocumentUpload.objects.filter(application=application).select_related('required_document'),
        'decrypted_password': decrypt_password(application.loan_password) if application.loan_password else None
    }
    
    return render(request, 'dashboard/see_application_details_admin.html', context)
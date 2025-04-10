from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from apps.accounts.views import agent_required, manager_required
from django.contrib.auth import get_user_model
from apps.loan.models import LoanApplication
from django.db.models import Count, Avg, Case, When, FloatField
from django.views.decorators.csrf import ensure_csrf_cookie

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
    return render(request, "dashboard/agent_dashboard.html", context)

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
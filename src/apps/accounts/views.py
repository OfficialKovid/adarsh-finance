from django.shortcuts import render, redirect
from .models import MyUser
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from apps.loan.models import LoanApplication
from django.db.models import Q

def signup(request):
    if request.user.is_authenticated:
        return redirect('account')
        
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        reference_number = request.POST.get("reference_number")
        
        # Validate email and password
        if not all([email, password, reference_number]):
            messages.error(request, 'All fields are required')
            return redirect('signup')
            
        # Check if email already exists
        if MyUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('signup')
            
        # Fetch application details
        application = LoanApplication.get_by_reference(reference_number)
        if not application:
            messages.error(request, 'Invalid reference number')
            return redirect('signup')
            
        # Create new user with application details
        try:
            user = MyUser.objects.create_user(
                email=email, 
                password=password,
                first_name=application.name.split()[0],
                last_name=application.name.split()[-1] if len(application.name.split()) > 1 else "",
                phone_number=application.phone_number,
                reference_number=reference_number  # Add this line
            )
            
            # Link user to application
            application.user = user
            application.is_registered = True
            application.save()
            
            # Automatically log in the user
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('account')
            else:
                messages.success(request, 'Account created successfully. Please login.')
                return redirect('login')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('signup')
            
    return render(request, "accounts/signup.html")

def login_page(request):
    if request.user.is_authenticated:
        return redirect('account')
        
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'account')  # Default to 'account' if no next parameter
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('login')
            
    return render(request, "accounts/login.html")

def staff_login(request):
    if request.user.is_authenticated:
        if request.user.role == 'AGENT':
            return redirect('dashboard:agent-dashboard')
        elif request.user.role == 'MANAGER':
            return redirect('dashboard:manager-dashboard')
        elif request.user.role == 'ADMIN':
            return redirect('admin:index')
        return redirect('account')
        
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.role in ['AGENT', 'MANAGER', 'ADMIN']:
            login(request, user)
            if user.role == 'AGENT':
                return redirect('dashboard:agent-dashboard')
            elif user.role == 'MANAGER':
                return redirect('dashboard:manager-dashboard')
            elif user.role == 'ADMIN':
                return redirect('admin:index')
        else:
            messages.error(request, 'Invalid staff credentials')
            return redirect('staff-login')
            
    return render(request, "accounts/staff_login.html")

# Keep the decorators here as they are used by dashboard app
def agent_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'AGENT':
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. Agent privileges required.')
        return redirect('staff-login')
    return wrapper

def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'MANAGER':
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. Manager privileges required.')
        return redirect('staff-login')
    return wrapper

@login_required(login_url='/login/')
def account(request):
    # Get the user's latest application where they are either the applicant or assigned agent
    latest_application = LoanApplication.objects.filter(
        Q(assigned_agent=request.user) | Q(name=request.user.get_full_name())
    ).first()
    
    context = {
        'user': request.user,
        'application': latest_application,
    }
    return render(request, 'accounts/account.html', context)

def logout_user(request):
    # Store the role before logout since we'll lose it after logout
    is_staff = request.user.role in ['AGENT', 'MANAGER', 'ADMIN']
    logout(request)
    # Redirect based on whether they were staff or customer
    if is_staff:
        return redirect('staff-login')
    return redirect('login')

from apps.loan.models import LoanApplication

def register_user(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            reference_number = form.cleaned_data['reference_number']
            
            # Get application by reference number
            application = LoanApplication.get_by_reference(reference_number)
            if not application:
                form.add_error('reference_number', 'Invalid or already registered reference number')
                return render(request, 'accounts/register.html', {'form': form})
            
            # Create user
            user = form.save()
            
            # Link application to user
            application.user = user
            application.is_registered = True
            application.save()
            
            # Log user in
            login(request, user)
            return redirect('home_page')
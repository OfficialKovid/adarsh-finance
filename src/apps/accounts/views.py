from django.shortcuts import render, redirect
from .models import MyUser
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from apps.loan.models import LoanApplication

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
                phone_number=application.phone_number
            )
            
            # Mark the reference number as used
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

@login_required(login_url='/login/')
def account(request):
    return render(request, "accounts/account.html")


def logout_user(request):
    logout(request)
    return redirect('/login/')
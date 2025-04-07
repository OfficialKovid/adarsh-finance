from django.shortcuts import render, redirect
from .models import MyUser
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def signup(request):
    if request.user.is_authenticated:
        return redirect('account')
        
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("firstName")
        last_name = request.POST.get("lastName")
        phone_number = request.POST.get("phone")
        
        # Validate required fields
        if not all([email, password, first_name, last_name, phone_number]):
            messages.error(request, 'All fields are required')
            return redirect('signup')
            
        # Check if email already exists
        if MyUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('signup')
            
        # Create new user
        try:
            user = MyUser.objects.create_user(
                email=email, 
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number
            )
            # Automatically log in the user after signup
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('account')  # Redirect to account page after successful signup
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
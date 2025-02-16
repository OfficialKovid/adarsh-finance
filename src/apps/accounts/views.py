from django.shortcuts import render, redirect
from .models import MyUser
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def signup(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if MyUser.objects.filter(email=email).exists():
            messages.info(request, 'Email already exists')
            return redirect('/signup/')

        user = MyUser.objects.create_user(email=email, password=password)
        user.save()
        return redirect('/login/')
    return render(request, "accounts/signup.html")

# If you want to use an email-based system in Django, you need to make some changes:
# 1. In admin.py, create a custom login system for emails because the default login system does not accept email by default.
# 2. Inherit the default User model and add an email field, ensuring it is unique since the default user ID is not valid for this purpose.
# 3. Update the settings to point to your custom user model:
#    AUTH_USER_MODEL = 'accounts.MyUser'




# Detial

# If you want to use an email-based authentication system in Django, here are the required steps:
# 1. Create a custom user model that inherits from AbstractBaseUser and PermissionsMixin.
#    - Add an email field and make it unique since emails will serve as the primary identifier instead of usernames.
#    - Ensure USERNAME_FIELD is set to 'email' and REQUIRED_FIELDS is empty or contains other required fields.
# 2. Implement a custom user manager to handle user creation (both regular users and superusers) with email and password.
# 3. Update the settings file to use your custom user model:
#    AUTH_USER_MODEL = 'accounts.MyUser'
# 4. In the admin panel (admin.py), customize the admin interface to work with the custom user model.
#    - Update list displays, search fields, and forms to handle email-based users.
# 5. Update or create custom authentication forms if necessary to ensure login and registration use the email field.
def login_page(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        if not MyUser.objects.filter(email=email).exists():
            messages.info(request, 'Wrong email')
            return redirect('/login/')

        user = authenticate(email=email, password=password)
        if user is None:
            messages.error(request, 'Wrong password')
            return redirect('/login/')
        else:
            login(request, user)
            
            # Get next parameter from URL
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            return redirect('/')

    return render(request, "accounts/login.html")

@login_required(login_url='/login/')
def account(request):
    return render(request, "accounts/account.html")

@login_required(login_url='/account/')
def orders(request):
    return render(request, "orders.html")

def logout_user(request):
    logout(request)
    return redirect('/login/')
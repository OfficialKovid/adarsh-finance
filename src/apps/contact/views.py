from django.shortcuts import render,redirect
from .models import *
from django.contrib import messages  # Add this import
from django.http import HttpResponse
# Create your views here.

def contact(request):
    if request.method == "POST":
        data = request.POST
        fullName = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')  # Add this line
        message = data.get('message')
        
        ContactMessage.objects.create(
            full_name=fullName,
            email=email,
            phone=phone,  # Add this line
            message=message,
        )
        messages.success(request, "Thank you for contacting us! Our customer service team will get back to you shortly.")
        return redirect('/contact/')
    
    return render(request,"contact.html")
from django.shortcuts import render,redirect
from .models import ContactMessage
from django.contrib import messages  


def contact(request):
    if request.method == "POST":
        data = request.POST
        fullName = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')  
        message = data.get('message')
        
        ContactMessage.objects.create(
            full_name=fullName,
            email=email,
            phone=phone,  
            message=message,
        )
        messages.success(request, "Thank you for contacting us! Our customer service team will get back to you shortly.")
        return redirect('/contact/')
    
    return render(request,"contact.html")
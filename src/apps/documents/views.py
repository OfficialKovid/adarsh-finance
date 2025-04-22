from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from apps.loan.models import LoanApplication
from .models import RequiredDocument, DocumentUpload
import os

@login_required
def upload_documents(request, application_id):
    application = get_object_or_404(LoanApplication, id=application_id, user=request.user)
    
    # Check if documents are already uploaded
    existing_uploads = DocumentUpload.objects.filter(application=application).exists()
    if existing_uploads:
        messages.info(request, "You have already uploaded documents for this application.")
        return render(request, 'customer/documents_submitted.html', {
            'application': application
        })
    
    if request.method == 'POST':
        try:
            required_docs = RequiredDocument.objects.filter(scheme=application.scheme)
            
            for doc in required_docs:
                file_key = f'doc_{doc.id}'
                if file_key in request.FILES:
                    file = request.FILES[file_key]
                    
                    # Create directory if it doesn't exist
                    upload_path = f'documents/{application.reference_number}/{doc.document_name}'
                    full_path = os.path.join(settings.MEDIA_ROOT, upload_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Save file
                    DocumentUpload.objects.create(
                        application=application,
                        required_document=doc,
                        file=file
                    )
            
            messages.success(request, "Documents uploaded successfully!")
            return render(request, 'customer/documents_submitted.html', {
                'application': application,
                'success': True
            })
            
        except Exception as e:
            messages.error(request, f"Error uploading documents: {str(e)}")
            return redirect('documents:upload', application_id=application_id)
    
    # For GET request
    required_documents = RequiredDocument.objects.filter(scheme=application.scheme)
    context = {
        'application': application,
        'scheme': application.scheme,
        'required_documents': required_documents
    }
    return render(request, 'customer/doc_upload.html', context)

@login_required
def remove_document(request, document_id):
    if request.method == 'POST':
        try:
            doc = get_object_or_404(DocumentUpload, 
                id=document_id, 
                application__user=request.user
            )
            doc.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})

@login_required
def view_documents(request, application_id):
    application = get_object_or_404(LoanApplication, id=application_id, user=request.user)
    documents = DocumentUpload.objects.filter(application=application)
    return render(request, 'customer/view_documents.html', {
        'application': application,
        'documents': documents
    })

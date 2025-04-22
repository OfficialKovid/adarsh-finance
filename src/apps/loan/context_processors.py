from apps.loan.models import LoanApplication

def loan_status(request):
    context = {
        'has_application': False,
        'active_scheme': None
    }
    
    if request.user.is_authenticated:
        # Get the most recent active application with updated status list
        active_application = LoanApplication.objects.filter(
            user=request.user,
            status__in=['new_lead', 'assigned', 'details_collected', 'document_collected', 
                       'form_filled', 'under_review']
        ).select_related('scheme').order_by('-applied_at').first()
        
        if active_application:
            context.update({
                'has_application': True,
                'active_scheme': active_application.scheme,
                'active_application': active_application
            })
    
    return context

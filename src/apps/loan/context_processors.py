from .models import LoanApplication
from django.db.models import Q

def loan_status(request):
    """Global context processor for loan application status"""
    if request.user.is_authenticated:
        # Check for applications where user is the applicant
        active_application = LoanApplication.objects.filter(
            Q(user=request.user) | Q(phone_number=request.user.phone_number),
            status__in=['new_lead', 'assigned', 'detail_collection', 'form_filled', 'under_review']
        ).select_related('scheme').first()

        return {
            'has_application': bool(active_application),
            'active_scheme': active_application.scheme if active_application else None,
            'active_application': active_application
        }
    return {
        'has_application': False,
        'active_scheme': None,
        'active_application': None
    }

from django.urls import path
from .views import list_loans, add_new_loan, loan_details, apply_loan, applications_list, update_application_status

urlpatterns = [
    path('loans/', list_loans, name='list_loans'),
    path('loans/add/', add_new_loan, name='add_new_loan'),
    path('loans/applications/', applications_list, name='applications_list'),  # Moved before slug pattern
    path('loans/applications/<int:application_id>/update-status/', update_application_status, name='update_application_status'),
    path('loans/<slug:slug>/apply/', apply_loan, name='apply_loan'),
    path('loans/<slug:slug>/', loan_details, name='loan_details'),  # Most generic pattern at the end
]
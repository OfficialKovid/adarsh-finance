from django.urls import path
from .views import (list_loans, add_new_loan, loan_details, apply_loan, 
                   applications_list, update_application_status, assign_agent, 
                   get_search_suggestions, manage_schemes, toggle_scheme_status)

urlpatterns = [
    path('loans/', list_loans, name='list_loans'),
    path('loans/add/', add_new_loan, name='add_new_loan'),
    path('loans/manage/', manage_schemes, name='manage_schemes'),  # Add this line
    path('loans/applications/', applications_list, name='applications_list'),  # Moved before slug pattern
    path('loans/applications/<int:application_id>/update-status/', update_application_status, name='update_application_status'),
    path('loans/applications/<int:application_id>/assign-agent/', assign_agent, name='assign_agent'),
    path('loans/search-suggestions/', get_search_suggestions, name='search_suggestions'),
    path('loans/<int:scheme_id>/toggle-status/', toggle_scheme_status, name='toggle_scheme_status'),
    # Removed edit scheme URL
    path('loans/<slug:slug>/apply/', apply_loan, name='apply_loan'),
    path('loans/<slug:slug>/', loan_details, name='loan_details'),  # Most generic pattern at the end
]
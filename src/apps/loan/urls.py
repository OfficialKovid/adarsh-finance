from django.urls import path
from .views import list_loans, add_new_loan, loan_details

urlpatterns = [
    path('loans/', list_loans, name='list_loans'),
    path('loans/add/', add_new_loan, name='add_new_loan'),
    path('loans/<slug:slug>/', loan_details, name='loan_details'),
]
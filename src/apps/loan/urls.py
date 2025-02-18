from django.urls import path
from .views import list_loans


urlpatterns = [
path('loans/', list_loans, name='list_loans'),
]
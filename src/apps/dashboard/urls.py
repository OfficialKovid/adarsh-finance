from django.urls import path
from .views import (
    dashboard, 
    agent_dashboard, 
    manager_dashboard, 
    agents_management,
    toggle_agent_status
)

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('agent/', agent_dashboard, name='agent-dashboard'),
    path('manager/', manager_dashboard, name='manager-dashboard'),
    path('manager/agents/', agents_management, name='agents-management'),
    path('manager/agents/<int:agent_id>/toggle/', toggle_agent_status, name='toggle-agent-status'),
]
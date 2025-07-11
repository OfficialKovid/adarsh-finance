from django.urls import path
from .views import (
    dashboard, 
    agent_dashboard, 
    manager_dashboard, 
    agents_management,
    toggle_agent_status,
    add_agent,
    assigned_applications,
    see_application_details,
    update_application_credentials,
    update_application_status,
    application_details_admin
)

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('agent/', agent_dashboard, name='agent-dashboard'),
    path('manager/', manager_dashboard, name='manager-dashboard'),
    path('manager/agents/', agents_management, name='agents-management'),
    path('manager/agents/<int:agent_id>/toggle/', toggle_agent_status, name='toggle-agent-status'),
    path('manager/agents/add/', add_agent, name='add-agent'),
    path('agent/applications/', assigned_applications, name='assigned-applications'),
    path('agent/applications/<int:application_id>/', see_application_details, name='see-application-details'),
    path('applications/<int:application_id>/update-credentials/', 
         update_application_credentials, 
         name='update_application_credentials'),
    path('application/<int:application_id>/update-status/', 
         update_application_status, 
         name='update_application_status'),
    path('applications/<int:application_id>/details/', 
         application_details_admin, 
         name='application_details_admin'),
]
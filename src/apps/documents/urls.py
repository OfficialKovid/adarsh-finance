from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('upload/<int:application_id>/', views.upload_documents, name='upload'),
    path('remove/<int:document_id>/', views.remove_document, name='remove'),
    path('view/<int:application_id>/', views.view_documents, name='view'),
]

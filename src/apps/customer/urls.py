from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('form/<slug:scheme_slug>/', views.fill_form, name='fill_form'),
    path('form/<slug:scheme_slug>/submit/', views.submit_form, name='submit_form'),
    path('track-application/', views.track_application, name='track_application'),
]

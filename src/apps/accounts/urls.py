from django.urls import path
from .views import signup, login_page, logout_user, account, staff_login

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', login_page, name='login'),
    path('logout/', logout_user, name='logout'),
    path('account/', account, name='account'),
    path('dashboard/staff-login/', staff_login, name='staff-login'),
]
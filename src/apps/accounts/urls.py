from django.urls import path
from .views import signup, login_page, logout_user, account

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', login_page, name='login'),  # Keep only this login path
    path('logout/', logout_user, name='logout'),
    path('account/', account, name='account'),
]
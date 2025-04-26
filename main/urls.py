from django.urls import path
from .views import *

app_name = 'main'
urlpatterns = [
    path('', dashboard, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/change-password/', change_password, name='change_password'),
]
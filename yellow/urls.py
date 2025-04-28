from django.urls import path
from .views import *

app_name = 'yellow'
urlpatterns = [
    path('hewan/', hewan_list_view, name='hewan_list'),
    path('habitat/', habitat_list_view, name='habitat_list'),
]
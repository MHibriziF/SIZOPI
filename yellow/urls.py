from django.urls import path
from .views import *

app_name = 'yellow'
urlpatterns = [
    path('hewan/', hewan_list_view, name='hewan_list'),
    path('hewan/tambah/', tambah_hewan_view, name='tambah_hewan'),
     path('hewan/hapus/<uuid:id>/', hapus_hewan_view, name='hapus_hewan'),
    path('habitat/', habitat_list_view, name='habitat_list'),
]
from django.urls import path
from .views import *

app_name = 'yellow'
urlpatterns = [
    path('hewan/', hewan_list_view, name='hewan_list'),
    path('hewan/tambah/', tambah_hewan_view, name='tambah_hewan'),
     path('hewan/hapus/<uuid:id>/', hapus_hewan_view, name='hapus_hewan'),
    path('habitat/', habitat_list_view, name='habitat_list'),
    path('habitat/tambah/', tambah_habitat_view, name='tambah_habitat'),
    path('habitat/hapus/<str:nama_habitat>/', hapus_habitat_view, name='hapus_habitat'),
    path('habitat/detail/<str:nama_habitat>/', habitat_detail_view, name='habitat_detail'),
]
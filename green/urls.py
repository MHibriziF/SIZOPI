# green/urls.py
from django.urls import path
from .views import *

app_name = 'green'
urlpatterns = [
    path('rekam_medis/', rekam_medis_list, name='rekam_medis_list'),
    path('rekam_medis/create/<uuid:id_hewan>/', rekam_medis_create, name='rekam_medis_create'),
    path('rekam_medis/update/<uuid:id_hewan>/<str:tanggal>/', rekam_medis_update, name='rekam_medis_update'),
    path('rekam_medis/delete/<uuid:id_hewan>/<str:tanggal>/', rekam_medis_delete, name='rekam_medis_delete'),
    
    path('jadwal_pemeriksaan/', jadwal_pemeriksaan_list, name='jadwal_pemeriksaan_list'),
    path('jadwal_pemeriksaan/create/<uuid:id_hewan>/', jadwal_pemeriksaan_create, name='jadwal_pemeriksaan_create'),
    
    path('pemberian_pakan/', pemberian_pakan_list, name='pemberian_pakan_list'),
    path('pemberian_pakan/riwayat/', riwayat_pemberian_pakan, name='riwayat_pemberian_pakan'),
    path('pemberian_pakan/create/<uuid:id_hewan>/', pemberian_pakan_create, name='pemberian_pakan_create'),
    path('pemberian_pakan/update/<uuid:id_hewan>/<str:jadwal>/', pemberian_pakan_update, name='pemberian_pakan_update'),
    path('pemberian_pakan/delete/<uuid:id_hewan>/<str:jadwal>/', pemberian_pakan_delete, name='pemberian_pakan_delete'),
    path('pemberian_pakan/beri/<uuid:id_hewan>/<str:jadwal>/', pemberian_pakan_beri, name='pemberian_pakan_beri'),
]
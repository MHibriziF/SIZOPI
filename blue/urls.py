from django.urls import path
from .views import *

app_name = 'blue'
urlpatterns = [
    path('reservasi/', reservasi, name='reservasi'),
    path('kelola-wahana/', kelola_wahana, name='kelola_wahana'),
    path('kelola-atraksi/', kelola_atraksi, name='kelola_atraksi'),
    path('kelola-pengunjung/', kelola_pengunjung, name='kelola_pengunjung'),
    path('delete-wahana/<str:nama_wahana>/', delete_wahana, name='delete_wahana'),
    path('delete-atraksi/<str:nama_atraksi>/', delete_atraksi, name='delete_atraksi'),
]

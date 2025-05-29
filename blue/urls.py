from django.urls import path
from .views import *

app_name = 'blue'
urlpatterns = [
    path('reservasi/', reservasi, name='reservasi'),
    path('kelola-wahana/', kelola_wahana, name='kelola_wahana'),
    path('kelola-atraksi/', kelola_atraksi, name='kelola_atraksi'),
    path('kelola-pengunjung/', kelola_pengunjung, name='kelola_pengunjung'),
    path('cancel-reservasi/', cancel_reservasi, name='cancel_reservasi'),
    path('delete-fasilitas/', delete_fasilitas, name='delete_fasilitas'),
]

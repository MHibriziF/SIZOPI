from django.urls import path
from . import views

app_name = 'adopsi'

urlpatterns = [
    path('api/check-user/', views.api_check_user, name='api_check_user'),
    path('api/get-adopter/', views.api_get_adopter, name='api_get_adopter'),

    # Manajemen Adopsi
    path('adoptions/', views.list_adoptions, name='list_adoptions'),
    path('adoption/create/<uuid:hewan_id>/', views.create_adoption, name='create_adoption'),
    path('adoption/<uuid:id_adopter>/<uuid:hewan_id>/<str:tgl_mulai>/update/', views.adoption_detail, name='update_adoption'),

    # Pengunjung/Adopter
    path('adoptions/<uuid:hewan_id>/<str:tgl_mulai>/certificate/', views.adoption_certificate, name='adoption_certificate'),
    path('adoptions/<uuid:hewan_id>/<str:tgl_mulai>/report/', views.adoption_report, name='adoption_report'),
    path('adoptions/<uuid:hewan_id>/<str:tgl_mulai>/extend/', views.extend_adoption, name='extend_adoption'),
    path('adoptions/<uuid:hewan_id>/<str:tgl_mulai>/stop/', views.stop_adoption_user, name='stop_adoption_user'),

    # Admin Manajemen Adopter
    path('adopters/', views.list_adopters, name='list_adopters'),
    path('adopters/<uuid:id_adopter>/history/', views.admin_adopter_history, name='admin_adopter_history'),
    path('adopters/<uuid:id_adopter>/delete/', views.admin_delete_adopter, name='admin_delete_adopter'),

    # Admin Hapus Data Adopsi yang Sudah Berakhir
    path('adoption/<uuid:id_adopter>/<uuid:hewan_id>/<str:tgl_mulai>/delete/', views.admin_delete_adoption, name='admin_delete_adoption'),
]

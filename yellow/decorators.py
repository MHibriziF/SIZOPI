from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.db import connection

def role_required(*allowed_roles):
    """
    Decorator untuk membatasi akses berdasarkan role user.
    
    Args:
        allowed_roles: Tuple berisi role yang diizinkan mengakses view
    
    Usage:
        @role_required('Dokter', 'Penjaga Hewan', 'Staf Administrasi')
        def some_view(request):
            # view logic
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Anda harus login untuk mengakses halaman ini.")
                return redirect('login')
            
            try:
                # Ambil role user dari database
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT role FROM SIZOPI.PENGGUNA 
                        WHERE username = %s
                    """, [request.user.username])
                    result = cursor.fetchone()
                
                if not result:
                    messages.error(request, "Data pengguna tidak ditemukan.")
                    return redirect('login')
                
                user_role = result[0]
                
                # Cek apakah role user termasuk dalam allowed_roles
                if user_role not in allowed_roles:
                    allowed_roles_str = ', '.join(allowed_roles)
                    messages.error(request, f"Akses ditolak. Halaman ini hanya dapat diakses oleh: {allowed_roles_str}")
                    return redirect('main:dashboard')  # Redirect ke dashboard atau halaman utama
                
                # Jika role sesuai, lanjutkan ke view
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                print(f"Error saat memeriksa role: {str(e)}")
                messages.error(request, "Terjadi kesalahan saat memeriksa hak akses.")
                return redirect('main:dashboard')
        
        return wrapper
    return decorator

def dokter_penjaga_admin_required(view_func):
    """
    Decorator khusus untuk view hewan (Dokter, Penjaga Hewan, Staf Administrasi)
    """
    return role_required('Dokter', 'Penjaga Hewan', 'Staf Administrasi')(view_func)

def penjaga_admin_required(view_func):
    """
    Decorator khusus untuk view habitat (Penjaga Hewan, Staf Administrasi)
    """
    return role_required('Penjaga Hewan', 'Staf Administrasi')(view_func)
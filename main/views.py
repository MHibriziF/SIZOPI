from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from utils.db_connection import execute_query, execute_transaction

def home(request):
    return render(request, 'main.html')

@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        nama_depan = request.POST.get("first_name")  
        nama_tengah = request.POST.get("middle_name") or None  
        nama_belakang = request.POST.get("last_name") 
        no_telepon = request.POST.get("phone")  
        role = request.POST.get("role")

        confirm_password = request.POST.get("confirm_password")
        if password != confirm_password:
            messages.error(request, "Password dan konfirmasi password tidak cocok.")
            return render(request, "register.html")

        sqls = [
            """
            INSERT INTO PENGGUNA
            (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
        ]
        params = [
            (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
        ]

        if role == "pengunjung":
            alamat = request.POST.get("role_field1")
            tgl_lahir = request.POST.get("role_field2")
            if not alamat or not tgl_lahir:
                messages.error(request, "Alamat dan tanggal lahir wajib diisi untuk pengunjung.")
                return render(request, "register.html")

            sqls.append("""
                INSERT INTO PENGUNJUNG
                (username_p, alamat, tgl_lahir)
                VALUES (%s, %s, %s)
            """)
            params.append((username, alamat, tgl_lahir))
        elif role == "dokter":
            no_str = request.POST.get("role_field1")
            if not no_str:
                messages.error(request, "Nomor STR wajib diisi untuk dokter hewan.")
                return render(request, "register.html")
                
            sqls.append("""
                INSERT INTO DOKTER_HEWAN
                (username_DH, no_STR)
                VALUES (%s, %s)
            """)
            params.append((username, no_str))
        elif role == "penjaga":
            sqls.append("""
                INSERT INTO PENJAGA_HEWAN
                (username_jh)
                VALUES (%s)
            """)
            params.append((username,))
        else:
            messages.error(request, "Peran tidak valid. Pilih pengunjung, dokter, atau penjaga.")
            return render(request, "register.html")

        success = execute_transaction(sqls, params)
        if success:
            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect("main:login")
        else:
            messages.error(request, "Registrasi gagal: username mungkin sudah terdaftar.")

    return render(request, "register.html")

@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        rows = execute_query(
            "SELECT password FROM PENGGUNA WHERE username = %s",
            (username,)
        )
        
        if rows and rows[0]["password"] == password:
            roles = []
            if execute_query("SELECT 1 FROM PENGUNJUNG WHERE username_p = %s", (username,)):
                roles.append("pengunjung")
            if execute_query("SELECT 1 FROM DOKTER_HEWAN WHERE username_DH = %s", (username,)):
                roles.append("dokter")
            if execute_query("SELECT 1 FROM PENJAGA_HEWAN WHERE username_jh = %s", (username,)):
                roles.append("penjaga")
            
            request.session["username"] = username
            request.session["roles"] = roles
            
            messages.success(request, f"Selamat datang, {username}!")
            return redirect("main:home")
        else:
            messages.error(request, "Username atau password salah.")

    return render(request, "login.html")

@require_http_methods(["GET", "POST"])
def logout(request):
    request.session.flush()
    messages.info(request, "Anda telah logout.")
    return redirect("main:login")
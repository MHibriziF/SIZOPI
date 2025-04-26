from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from utils.db_connection import execute_query, execute_transaction
import uuid

def home(request):
    return render(request, 'main.html')

@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        nama_depan = request.POST.get("first_name")
        nama_tengah = request.POST.get("middle_name") or None
        nama_belakang = request.POST.get("last_name")
        no_telepon = request.POST.get("phone")
        role = request.POST.get("role")
        
        if password != confirm_password:
            messages.error(request, "Password dan konfirmasi password tidak cocok.")
            return render(request, "register.html")
            
        existing_user = execute_query(
            "SELECT username FROM PENGGUNA WHERE username = %s",
            (username,)
        )
        
        if existing_user:
            messages.error(request, "Username sudah digunakan. Silakan pilih username lain.")
            return render(request, "register.html")
            
        existing_email = execute_query(
            "SELECT email FROM PENGGUNA WHERE email = %s",
            (email,)
        )
        
        if existing_email:
            messages.error(request, "Email sudah digunakan. Silakan gunakan email lain.")
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
            spesialisasi = request.POST.getlist("spesialisasi")
            
            if not no_str:
                messages.error(request, "Nomor STR wajib diisi untuk dokter hewan.")
                return render(request, "register.html")
                
            if not spesialisasi:
                messages.error(request, "Pilih minimal satu spesialisasi.")
                return render(request, "register.html")
                
            sqls.append("""
                INSERT INTO DOKTER_HEWAN
                (username_DH, no_STR)
                VALUES (%s, %s)
            """)
            params.append((username, no_str))
            
            for spec in spesialisasi:
                sqls.append("""
                    INSERT INTO SPESIALISASI
                    (username_SH, nama_spesialis)
                    VALUES (%s, %s)
                """)
                params.append((username, spec))
                
        elif role == "penjaga":
            id_staf = str(uuid.uuid4())
            sqls.append("""
                INSERT INTO PENJAGA_HEWAN
                (username_jh, id_staf)
                VALUES (%s, %s)
            """)
            params.append((username, id_staf))
            
        elif role == "admin":
            id_staf = str(uuid.uuid4())
            sqls.append("""
                INSERT INTO STAF_ADMIN
                (username_sa, id_staf)
                VALUES (%s, %s)
            """)
            params.append((username, id_staf))
            
        elif role == "pelatih":
            id_staf = str(uuid.uuid4())
            sqls.append("""
                INSERT INTO PELATIH_HEWAN
                (username_lh, id_staf)
                VALUES (%s, %s)
            """)
            params.append((username, id_staf))
            
        else:
            messages.error(request, "Peran tidak valid. Pilih pengunjung, dokter, atau staff.")
            return render(request, "register.html")

        success = execute_transaction(sqls, params)
        if success:
            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect("main:login")
        else:
            messages.error(request, "Registrasi gagal: terjadi kesalahan pada sistem.")

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
            if execute_query("SELECT 1 FROM STAF_ADMIN WHERE username_sa = %s", (username,)):
                roles.append("admin")
            if execute_query("SELECT 1 FROM PELATIH_HEWAN WHERE username_lh = %s", (username,)):
                roles.append("pelatih")
            
            user_data = execute_query(
                "SELECT nama_depan, nama_belakang FROM PENGGUNA WHERE username = %s",
                (username,)
            )
            
            request.session["username"] = username
            request.session["roles"] = roles
            request.session["full_name"] = f"{user_data[0]['nama_depan']} {user_data[0]['nama_belakang']}"
            
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

def profile(request):
    if not request.session.get('username'):
        return redirect('main:login')
        
    username = request.session.get('username')
    
    user_data = execute_query(
        """
        SELECT p.*, 
               CASE 
                   WHEN dh.username_DH IS NOT NULL THEN 'dokter' 
                   WHEN pj.username_jh IS NOT NULL THEN 'penjaga' 
                   WHEN sa.username_sa IS NOT NULL THEN 'admin' 
                   WHEN ph.username_lh IS NOT NULL THEN 'pelatih' 
                   WHEN pg.username_p IS NOT NULL THEN 'pengunjung' 
               END as role
        FROM PENGGUNA p
        LEFT JOIN DOKTER_HEWAN dh ON p.username = dh.username_DH
        LEFT JOIN PENJAGA_HEWAN pj ON p.username = pj.username_jh
        LEFT JOIN STAF_ADMIN sa ON p.username = sa.username_sa
        LEFT JOIN PELATIH_HEWAN ph ON p.username = ph.username_lh
        LEFT JOIN PENGUNJUNG pg ON p.username = pg.username_p
        WHERE p.username = %s
        """,
        (username,)
    )
    
    if not user_data:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect('main:home')
        
    role = user_data[0]['role']
    
    additional_data = {}
    if role == 'dokter':
        additional_data = execute_query(
            "SELECT no_STR FROM DOKTER_HEWAN WHERE username_DH = %s",
            (username,)
        )[0]
        
        spesialisasi = execute_query(
            "SELECT nama_spesialis FROM SPESIALISASI WHERE username_SH = %s",
            (username,)
        )
        additional_data['spesialisasi'] = [s['nama_spesialis'] for s in spesialisasi]
        
    elif role == 'pengunjung':
        additional_data = execute_query(
            "SELECT alamat, tgl_lahir FROM PENGUNJUNG WHERE username_p = %s",
            (username,)
        )[0]
        
        adopter_data = execute_query(
            "SELECT id_adopter FROM ADOPTER WHERE username_adopter = %s",
            (username,)
        )
        
        if adopter_data:
            additional_data['is_adopter'] = True
            additional_data['id_adopter'] = adopter_data[0]['id_adopter']
        else:
            additional_data['is_adopter'] = False
            
    elif role == 'penjaga':
        additional_data = execute_query(
            "SELECT id_staf FROM PENJAGA_HEWAN WHERE username_jh = %s",
            (username,)
        )[0]
        
    elif role == 'admin':
        additional_data = execute_query(
            "SELECT id_staf FROM STAF_ADMIN WHERE username_sa = %s",
            (username,)
        )[0]
        
    elif role == 'pelatih':
        additional_data = execute_query(
            "SELECT id_staf FROM PELATIH_HEWAN WHERE username_lh = %s",
            (username,)
        )[0]
    
    context = {
        'user_data': user_data[0],
        'additional_data': additional_data,
        'role': role
    }
    
    return render(request, 'profile.html', context)

def dashboard(request):
    if not request.session.get('username'):
        return redirect('main:login')
        
    username = request.session.get('username')
    roles = request.session.get('roles', [])
    
    context = {
        'username': username,
        'roles': roles
    }
    
    return render(request, 'dashboard.html', context)
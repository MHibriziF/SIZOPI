from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from utils.db_connection import execute_query, execute_transaction
import uuid
import datetime

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
            return redirect("main:dashboard")
        else:
            messages.error(request, "Username atau password salah.")

    return render(request, "login.html")

@require_http_methods(["GET", "POST"])
def logout(request):
    request.session.flush()
    messages.info(request, "Anda telah logout.")
    return redirect("main:login")

def dashboard(request):
    if not request.session.get('username'):
        return redirect('main:login')
        
    username = request.session.get('username')
    roles = request.session.get('roles', [])
    
    user_data = execute_query(
        """
        SELECT username, email, nama_depan, nama_tengah, nama_belakang, no_telepon
        FROM PENGGUNA
        WHERE username = %s
        """,
        (username,)
    )[0]
    
    context = {
        'user_data': user_data,
        'roles': roles
    }
    
    if 'pengunjung' in roles:
        pengunjung_data = execute_query(
            """
            SELECT alamat, tgl_lahir
            FROM PENGUNJUNG
            WHERE username_p = %s
            """,
            (username,)
        )[0]
        
        riwayat_kunjungan = [
            {'tanggal': '2025-04-20', 'durasi': '3 jam'},
            {'tanggal': '2025-03-15', 'durasi': '2 jam'},
            {'tanggal': '2025-02-10', 'durasi': '4 jam'}
        ]
        
        tiket = [
            {'id': 'T12345', 'tanggal': '2025-04-26', 'jenis': 'Reguler', 'status': 'Valid'},
            {'id': 'T12245', 'tanggal': '2025-03-15', 'jenis': 'Reguler', 'status': 'Expired'}
        ]
        
        context.update({
            'pengunjung_data': pengunjung_data,
            'riwayat_kunjungan': riwayat_kunjungan,
            'tiket': tiket
        })
    
    elif 'dokter' in roles:
        dokter_data = execute_query(
            """
            SELECT no_STR
            FROM DOKTER_HEWAN
            WHERE username_DH = %s
            """,
            (username,)
        )[0]
        
        spesialisasi = execute_query(
            """
            SELECT nama_spesialis
            FROM SPESIALISASI
            WHERE username_SH = %s
            """,
            (username,)
        )
        
        jumlah_hewan = execute_query(
            """
            SELECT COUNT(DISTINCT id_hewan) as jumlah
            FROM CATATAN_MEDIS
            WHERE username_dh = %s
            """,
            (username,)
        )[0]['jumlah']
        
        context.update({
            'dokter_data': dokter_data,
            'spesialisasi': [s['nama_spesialis'] for s in spesialisasi],
            'jumlah_hewan': jumlah_hewan
        })
    
    elif 'penjaga' in roles:
        penjaga_data = execute_query(
            """
            SELECT id_staf
            FROM PENJAGA_HEWAN
            WHERE username_jh = %s
            """,
            (username,)
        )[0]
        
        jumlah_pakan = execute_query(
            """
            SELECT COUNT(*) as jumlah
            FROM MEMBERI
            WHERE username_jh = %s
            """,
            (username,)
        )[0]['jumlah']
        
        context.update({
            'penjaga_data': penjaga_data,
            'jumlah_pakan': jumlah_pakan
        })
    
    elif 'admin' in roles:
        admin_data = execute_query(
            """
            SELECT id_staf
            FROM STAF_ADMIN
            WHERE username_sa = %s
            """,
            (username,)
        )[0]
        
        statistik_admin = {
            'penjualan_hari_ini': 52,
            'pengunjung_hari_ini': 120,
            'pendapatan_mingguan': 'Rp 15,750,000'
        }
        
        context.update({
            'admin_data': admin_data,
            'statistik': statistik_admin
        })
    
    elif 'pelatih' in roles:
        pelatih_data = execute_query(
            """
            SELECT id_staf
            FROM PELATIH_HEWAN
            WHERE username_lh = %s
            """,
            (username,)
        )[0]
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        jadwal_hari_ini = execute_query(
            """
            SELECT j.nama_atraksi, j.tgl_penugasan
            FROM JADWAL_PENUGASAN j
            INNER JOIN ATRAKSI a ON j.nama_atraksi = a.nama_atraksi
            WHERE j.username_lh = %s AND DATE(j.tgl_penugasan) = %s
            """,
            (username, today)
        )
        
        hewan_dilatih = [
            {'id': 'H001', 'nama': 'Leo', 'spesies': 'Singa', 'status': 'Siap'},
            {'id': 'H005', 'nama': 'Milo', 'spesies': 'Gajah', 'status': 'Latihan'},
            {'id': 'H012', 'nama': 'Coco', 'spesies': 'Simpanse', 'status': 'Istirahat'}
        ]
        
        context.update({
            'pelatih_data': pelatih_data,
            'jadwal_hari_ini': jadwal_hari_ini,
            'hewan_dilatih': hewan_dilatih
        })
    
    return render(request, 'dashboard.html', context)

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

@require_http_methods(["GET", "POST"])
def edit_profile(request):
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
    
    if request.method == "POST":
        email = request.POST.get("email")
        nama_depan = request.POST.get("nama_depan")
        nama_tengah = request.POST.get("nama_tengah") or None
        nama_belakang = request.POST.get("nama_belakang")
        no_telepon = request.POST.get("no_telepon")
        
        sql = """
            UPDATE PENGGUNA
            SET email = %s, nama_depan = %s, nama_tengah = %s, nama_belakang = %s, no_telepon = %s
            WHERE username = %s
        """
        params = (email, nama_depan, nama_tengah, nama_belakang, no_telepon, username)
        
        success = execute_query(sql, params)
        
        if role == 'pengunjung':
            alamat = request.POST.get("alamat")
            tgl_lahir = request.POST.get("tgl_lahir")
            
            sql = """
                UPDATE PENGUNJUNG
                SET alamat = %s, tgl_lahir = %s
                WHERE username_p = %s
            """
            params = (alamat, tgl_lahir, username)
            success = execute_query(sql, params)
            
        elif role == 'dokter':
            sql = "DELETE FROM SPESIALISASI WHERE username_SH = %s"
            params = (username,)
            execute_query(sql, params)
            
            spesialisasi = request.POST.getlist("spesialisasi")
            for spec in spesialisasi:
                sql = "INSERT INTO SPESIALISASI (username_SH, nama_spesialis) VALUES (%s, %s)"
                params = (username, spec)
                execute_query(sql, params)
        
        if success:
            messages.success(request, "Profil berhasil diperbarui.")
            request.session["full_name"] = f"{nama_depan} {nama_belakang}"
            return redirect('main:profile')
        else:
            messages.error(request, "Gagal memperbarui profil.")
    
    context = {
        'user_data': user_data[0],
        'additional_data': additional_data,
        'role': role
    }
    
    return render(request, 'edit_profile.html', context)

@require_http_methods(["GET", "POST"])
def change_password(request):
    if not request.session.get('username'):
        return redirect('main:login')
        
    username = request.session.get('username')
    
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        
        current_password = execute_query(
            "SELECT password FROM PENGGUNA WHERE username = %s",
            (username,)
        )[0]['password']
        
        if old_password != current_password:
            messages.error(request, "Password lama tidak sesuai.")
            return render(request, "change_password.html")
            
        if new_password != confirm_password:
            messages.error(request, "Password baru dan konfirmasi tidak cocok.")
            return render(request, "change_password.html")
            
        sql = "UPDATE PENGGUNA SET password = %s WHERE username = %s"
        params = (new_password, username)
        
        success = execute_query(sql, params)
        
        if success:
            messages.success(request, "Password berhasil diubah.")
            return redirect('main:profile')
        else:
            messages.error(request, "Gagal mengubah password.")
    
    return render(request, 'change_password.html')
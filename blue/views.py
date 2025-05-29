from django.shortcuts import render, redirect
from utils.db_connection import execute_query, execute_transaction
from django.db import connection, DatabaseError
from .decorators import admin_required
from datetime import datetime
from django.contrib import messages

def query_fasilitas(fasilitas : str, field : str) -> str:
    return f"""
        SELECT 
            fa.nama_{fasilitas},
            fa.{field},
            TO_CHAR(f.jadwal, 'HH24:MI') AS jam 
        FROM {fasilitas} fa
        JOIN FASILITAS f ON fa.nama_{fasilitas} = f.nama
        ORDER BY nama_{fasilitas};
    """

def reservasi(request):
    if not request.session.get('username'):
        return redirect('main:login')
    if 'pengunjung' not in request.session.get('roles') and 'admin' not in request.session.get('roles'):
        return redirect('main:dashboard')
    if request.method == 'POST':
        return post_reservasi(request)
    return get_reservasi(request)

def get_reservasi(request):
    if not request.session.get('username'):
        return redirect('main:login')
    
    if 'pengunjung' not in request.session.get('roles') and 'admin' not in request.session.get('roles'):
        return redirect('main:dashboard')
    
    tanggal_hari_ini = datetime.now().date()
    data_wahana = execute_query(query_fasilitas("wahana", "peraturan"))
    data_atraksi = execute_query(query_fasilitas("atraksi", "lokasi"))
    data_fasilitas = {
        'data_atraksi': data_atraksi,
        'data_wahana': data_wahana
    }

    query_atraksi = """
        SELECT 
            r.nama_fasilitas,
            a.lokasi,
            TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
            TO_CHAR(r.tanggal_kunjungan, 'YYYY-MM-DD') AS tanggal,
            r.jumlah_tiket AS tiket,
            r.status,
            r.username_p
        FROM RESERVASI r
        JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
        JOIN FASILITAS f ON a.nama_atraksi = f.nama
    """

    query_wahana = """
        SELECT 
            r.nama_fasilitas,
            string_to_array(w.peraturan, ';') AS peraturan,
            TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
            TO_CHAR(r.tanggal_kunjungan, 'YYYY-MM-DD') AS tanggal,
            r.jumlah_tiket AS tiket,
            r.status,
            r.username_p
        FROM RESERVASI r
        JOIN WAHANA w ON r.nama_fasilitas = w.nama_wahana
        JOIN FASILITAS f ON w.nama_wahana = f.nama
    """

    query_reservasi = f"""
        SELECT * FROM (
            SELECT
                'Atraksi' AS jenis_reservasi,
                a.nama_atraksi AS nama_fasilitas,
                a.lokasi as lokasi_or_peraturan,
                TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
                TO_CHAR(r.tanggal_kunjungan, 'YYYY-MM-DD') AS tanggal,
                r.jumlah_tiket AS tiket,
                r.status,
                r.username_p
            FROM RESERVASI r
            JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
            JOIN FASILITAS f ON a.nama_atraksi = f.nama

            UNION ALL

            SELECT
                'Wahana' AS jenis_reservasi,
                w.nama_wahana AS nama_fasilitas,
                w.peraturan as lokasi_or_peraturan,
                TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
                TO_CHAR(r.tanggal_kunjungan, 'YYYY-MM-DD') AS tanggal,
                r.jumlah_tiket AS tiket,
                r.status,
                r.username_p
            FROM RESERVASI r
            JOIN WAHANA w ON r.nama_fasilitas = w.nama_wahana
            JOIN FASILITAS f ON w.nama_wahana = f.nama
        ) AS semua_reservasi
    """

    query_reservasi_fasilitas = """
        SELECT 
            f.nama,
            TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD') AS tanggal,
            TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
            CASE 
                WHEN a.nama_atraksi IS NOT NULL THEN 'Atraksi'
                WHEN w.nama_wahana IS NOT NULL THEN 'Wahana'
                ELSE 'Unknown'
            END AS jenis,
            (f.kapasitas_max - COALESCE(SUM(r.jumlah_tiket) , 0)) AS tiket_tersedia,
            (f.kapasitas_max - COALESCE(SUM(r.jumlah_tiket), 0))::text || ' dari ' || f.kapasitas_max::text AS kapasitas_tersedia,
            CASE 
                WHEN a.nama_atraksi IS NOT NULL THEN a.lokasi
                WHEN w.nama_wahana IS NOT NULL THEN w.peraturan
                ELSE NULL
            END AS lokasi_or_peraturan
        FROM FASILITAS f
        LEFT JOIN ATRAKSI a ON f.nama = a.nama_atraksi
        LEFT JOIN WAHANA w ON f.nama = w.nama_wahana
        LEFT JOIN RESERVASI r ON f.nama = r.nama_fasilitas 
            AND r.tanggal_kunjungan = CURRENT_DATE
            AND r.status = 'Terjadwal'
        GROUP BY f.nama, f.kapasitas_max, a.nama_atraksi, w.nama_wahana, a.lokasi, w.peraturan
        ORDER BY f.nama;
    """
    params = []
    if 'admin' in request.session.get("roles", []):
        query_atraksi += " ORDER BY r.tanggal_kunjungan DESC;"
        query_wahana += " ORDER BY r.tanggal_kunjungan DESC;"
        query_reservasi += " ORDER BY tanggal DESC, jam ASC;"
        roles = "admin"
    else:
        query_atraksi += " WHERE r.username_p = %s ORDER BY r.tanggal_kunjungan DESC;"
        query_wahana += " WHERE r.username_p = %s ORDER BY r.tanggal_kunjungan DESC;"
        query_reservasi += " WHERE username_p = %s ORDER BY tanggal DESC, jam ASC;"
        params = [request.session.get("username")]
        roles = "pengunjung"

    data_reservasi = execute_query(query_reservasi, params)
    data_reservasi_atraksi = execute_query(query_atraksi, params)
    data_reservasi_wahana = execute_query(query_wahana, params)
    data_reservasi_fasilitas = execute_query(query_reservasi_fasilitas)

    context = {
        'data_fasilitas': data_fasilitas,
        'data_reservasi_fasilitas': data_reservasi_fasilitas,
        'data_reservasi': data_reservasi, 
        'data_reservasi_atraksi': data_reservasi_atraksi,
        'data_reservasi_wahana': data_reservasi_wahana,
        'roles': roles,
    }

    return render(request, 'reservasi.html', context)

def is_editing_reservasi(request):
    return request.POST.get("nama_reservasi_wahana_diedit") or request.POST.get("nama_reservasi_atraksi_diedit") 

def post_reservasi(request):
    username_p = request.POST.get("username_p")  or request.session.get("username")
    nama_fasilitas = request.POST.get("nama_atraksi") or request.POST.get("nama_wahana")
    tanggal = request.POST.get("tanggal")
    jumlah_tiket = request.POST.get("tiket")

    if is_editing_reservasi(request):
        nama_fasilitas_lama = request.POST.get("nama_reservasi_wahana_diedit") or request.POST.get("nama_reservasi_atraksi_diedit")
        tanggal_lama = request.POST.get("tanggal_reservasi_diedit")
    
        check_reservasi = execute_query(
            "SELECT 1 FROM RESERVASI WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s AND status = 'Terjadwal'",
            [username_p, nama_fasilitas_lama, tanggal_lama]
        )
    
        if not check_reservasi:
            messages.error(request, "Reservasi gagal: Reservasi yang ingin diedit sudah dibatalkan", extra_tags='reservasi')
            return redirect('blue:reservasi')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE RESERVASI
                    SET nama_fasilitas = %s, tanggal_kunjungan = %s, jumlah_tiket = %s
                    WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s
                """, [nama_fasilitas, tanggal, int(jumlah_tiket), username_p, nama_fasilitas_lama, tanggal_lama])
        except DatabaseError as e:
            messages.error(request, f"{str(e)}", extra_tags='reservasi')
            return redirect('blue:reservasi')
        
        messages.success(request, "Reservasi berhasil diperbarui", extra_tags='reservasi')
        return redirect('/reservasi?tab=semua') 

    not_valid_reservation = execute_query(
        "SELECT * FROM RESERVASI WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s", 
        [username_p, nama_fasilitas, tanggal], 
    )
  
    if not_valid_reservation:
        messages.error(request, "Reservasi gagal: Anda telah membuat reservasi untuk fasilitas ini pada tanggal tersebut", extra_tags='reservasi')
        return redirect('blue:reservasi')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO RESERVASI (username_p, nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status)
                VALUES (%s, %s, %s, %s, %s)
            """, [username_p, nama_fasilitas, tanggal, int(jumlah_tiket), "Terjadwal"])
    except DatabaseError as e:
        messages.error(request, f"{str(e)}", extra_tags='reservasi')
        return redirect('blue:reservasi')
    messages.success(request, "Reservasi berhasil dibuat", extra_tags='reservasi')
    return redirect('/reservasi?tab=semua') 


def cancel_reservasi(request):
    if not request.session.get('username'):
        return redirect('main:login')

    username_p = request.POST.get("username_p")
    nama_fasilitas = request.POST.get("nama_fasilitas")
    tanggal = request.POST.get("tanggal_kunjungan")
    print(username_p, nama_fasilitas, tanggal)

    # Cek apakah reservasi masih terjadwal
    check_reservasi = execute_query(
        "SELECT 1 FROM RESERVASI WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s AND STATUS = 'Terjadwal'",
        [username_p, nama_fasilitas, tanggal]
    )

    if not check_reservasi:
        messages.error(request, "Reservasi sudah dibatalkan", extra_tags='reservasi')
        return redirect('blue:reservasi')
    
    # Batalkan reservasi
    execute_query(
        "UPDATE RESERVASI SET status = 'Dibatalkan' WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s", 
        [username_p, nama_fasilitas, tanggal],
    )
    
    messages.success(request, "Reservasi berhasil dibatalkan", extra_tags='reservasi')
    return redirect('blue:reservasi')

@admin_required
def kelola_wahana(request):
    if request.method == 'POST':
        return post_kelola_wahana(request)
    return get_kelola_wahana(request)

def get_kelola_wahana(request):
    query = """
        SELECT 
            w.nama_wahana,
            f.kapasitas_max AS kapasitas,
            TO_CHAR(F.jadwal, 'HH24:MI') AS jadwal,
            string_to_array(w.peraturan, ';') AS peraturan
        FROM WAHANA w
        JOIN FASILITAS F ON w.nama_wahana = F.nama
    """
    data_wahana = execute_query(query)
    context = {
        'data_wahana' : data_wahana,
    }
    
    return render(request, 'wahana.html', context)

def post_kelola_wahana(request):
    nama_lama = request.POST.get('nama_wahana_lama')
    nama_wahana = request.POST.get('nama_wahana')
    kapasitas = request.POST.get('kapasitas')
    jadwal = request.POST.get('jadwal')
    tanggal_hari_ini = datetime.now().date()
    jadwal_str = f"{tanggal_hari_ini} {jadwal}"
    peraturan_list = request.POST.getlist('peraturan[]')
    peraturan_str = ';'.join([p.strip() for p in peraturan_list if p.strip()])

    queries = []
    params = []
    if nama_lama: # Jika ada nama lama, artinya update data
        query_fasilitas = """
            UPDATE FASILITAS SET nama=%s, kapasitas_max=%s, jadwal=%s
            WHERE nama=%s
        """
        queries.append(query_fasilitas)
        params.append((nama_wahana, kapasitas, jadwal_str, nama_lama))

        query_wahana = """
            UPDATE WAHANA SET peraturan=%s
            WHERE nama_wahana=%s
        """
        queries.append(query_wahana)
        params.append((peraturan_str, nama_wahana))

    else:
        # Simpan ke FASILITAS
        query_fasilitas = """
            INSERT INTO FASILITAS (nama, kapasitas_max, jadwal)
            VALUES (%s, %s, %s)
        """

        queries.append(query_fasilitas)
        params.append((nama_wahana, kapasitas, jadwal_str))

        # Simpan ke WAHANA
        query_wahana = """
            INSERT INTO WAHANA (nama_wahana, peraturan)
            VALUES (%s, %s)
        """

        queries.append(query_wahana)
        params.append((nama_wahana, peraturan_str))

    result = execute_transaction(queries, params)
    if result:
        pesan = "Wahana berhasil diperbarui" if nama_lama else "Wahana berhasil disimpan"
        messages.success(request, pesan, extra_tags='wahana')
    else:
        pesan = "Wahana gagal diperbarui, pastikan nama fasilitas unik" if nama_lama else "Wahana gagal disimpan, pastikan nama fasilitas unik"
        messages.error(request, pesan, extra_tags='wahana')
     
    return redirect('blue:kelola_wahana')


@admin_required
def kelola_atraksi(request):
    if request.method == 'POST':
        return post_kelola_atraksi(request)
    return get_kelola_atraksi(request)

def get_kelola_atraksi(request):
    data_atraksi = execute_query("""
        SELECT 
            a.nama_atraksi,
            a.lokasi,
            f.kapasitas_max AS kapasitas,
            TO_CHAR(F.jadwal, 'HH24:MI') AS jadwal,
            ARRAY_AGG(DISTINCT (h.spesies || ' - ' || h.nama)) AS hewan_terlibat,
            ARRAY_AGG(DISTINCT h.id) AS id_hewan_terlibat,                                 
            STRING_AGG(DISTINCT
                (p.nama_depan || ' ' || COALESCE(p.nama_tengah || ' ', '') || p.nama_belakang), ', '
            ) AS pelatih,
            ARRAY_AGG(DISTINCT p.username) AS pelatih_terpilih
        FROM ATRAKSI a
        JOIN FASILITAS f ON a.nama_atraksi = f.nama
        LEFT JOIN BERPARTISIPASI b ON f.nama = b.nama_fasilitas
        LEFT JOIN HEWAN h ON b.id_hewan = h.id
        LEFT JOIN JADWAL_PENUGASAN j ON a.nama_atraksi = j.nama_atraksi
        LEFT JOIN PENGGUNA p ON j.username_lh = p.username
        GROUP BY a.nama_atraksi, a.lokasi, f.kapasitas_max, f.jadwal
        ORDER BY a.nama_atraksi, f.jadwal;
    """)
    
    data_pelatih = execute_query("""
        SELECT username, nama_depan, nama_tengah, nama_belakang
        FROM PENGGUNA p
        JOIN PELATIH_HEWAN ph ON p.username = ph.username_lh
        ORDER BY nama_depan, nama_tengah, nama_belakang asc;
    """)
 
    data_hewan = execute_query("""
        SELECT id, spesies, nama
        FROM HEWAN ORDER BY spesies, nama asc;
    """)

    context = {
        'data_atraksi' : data_atraksi,
        'data_hewan': data_hewan,
        'data_pelatih' : data_pelatih,
    }
    
    return render(request, 'atraksi.html', context)

def post_kelola_atraksi(request):
    def insert_pelatih(pelatih_list, queries, params):
        for username in pelatih_list:
            query_insert_jadwal = """
                INSERT INTO JADWAL_PENUGASAN (nama_atraksi, username_lh, tgl_penugasan) VALUES (%s, %s, %s)
            """
            queries.append(query_insert_jadwal)
            params.append((nama_atraksi, username, jadwal_str))
    def insert_hewan(hewan_list, queries, params):  
        for id_hewan in hewan_list:
            query_insert_hewan = """
                INSERT INTO BERPARTISIPASI (nama_fasilitas, id_hewan) VALUES (%s, %s)
            """
            queries.append(query_insert_hewan)
            params.append((nama_atraksi, id_hewan))

    nama_lama = request.POST.get('nama_atraksi_lama')  
    nama_atraksi = request.POST.get('nama_atraksi')
    lokasi = request.POST.get('lokasi')
    kapasitas = request.POST.get('kapasitas')
    jadwal = request.POST.get('jadwal')  
    pelatih_list = request.POST.getlist('pelatih')
    hewan_list = request.POST.getlist('hewan_terlibat')
    
    tanggal_hari_ini = datetime.now().date()
    jadwal_str = f"{tanggal_hari_ini} {jadwal}"

    queries = []
    params = []

    if nama_lama:  # Jika ada nama lama, artinya update atraksi 
        query_update_fasilitas = """
            UPDATE FASILITAS SET nama = %s, kapasitas_max = %s, jadwal = %s WHERE nama = %s
        """
        queries.append(query_update_fasilitas)
        params.append((nama_atraksi, kapasitas, jadwal_str, nama_lama))

        query_update_atraksi = """
            UPDATE ATRAKSI SET lokasi = %s WHERE nama_atraksi = %s
        """
        queries.append(query_update_atraksi)
        params.append((lokasi, nama_atraksi))
        
        # Ambil data pelatih lama
        pelatih_lama = execute_query("SELECT username_lh FROM JADWAL_PENUGASAN WHERE nama_atraksi = %s", [nama_lama])
        pelatih_lama = set(row['username_lh'] for row in pelatih_lama)
        pelatih_update = set(pelatih_list)

        # hapus data lama
        pelatih_yang_dihapus = pelatih_lama - pelatih_update
        for username in pelatih_yang_dihapus:
            queries.append("""
                DELETE FROM JADWAL_PENUGASAN WHERE nama_atraksi = %s AND username_lh = %s
            """)
            params.append((nama_atraksi, username))
        queries.append("DELETE FROM BERPARTISIPASI WHERE nama_fasilitas = %s")
        params.append((nama_atraksi,))

        # insert ulang data 
        pelatih_yang_baru = pelatih_update - pelatih_lama
        insert_pelatih(pelatih_yang_baru, queries, params)
        insert_hewan(hewan_list, queries, params)
    else:  
        query_fasilitas = """
            INSERT INTO FASILITAS (nama, kapasitas_max, jadwal) VALUES (%s, %s, %s)
        """
        queries.append(query_fasilitas)
        params.append((nama_atraksi, kapasitas, jadwal_str))

        query_atraksi = """
            INSERT INTO ATRAKSI (nama_atraksi, lokasi) VALUES (%s, %s)
        """
        queries.append(query_atraksi)
        params.append((nama_atraksi, lokasi))

        insert_pelatih(pelatih_list, queries, params)
        insert_hewan(hewan_list, queries, params)

    result = execute_transaction(queries, params)

    if result:
        if nama_lama:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT rotasi_oto_pelatih_func(%s);", [nama_atraksi])
                    result_edit = cursor.fetchone()
                    if result_edit:
                        pesan = result_edit[0]
                        messages.success(request, pesan, extra_tags='atraksi')
                    messages.success(request, "Atraksi berhasil diupdate", extra_tags='atraksi')
            except DatabaseError as e:
                messages.error(request, f"{str(e)}", extra_tags='atraksi')
                return redirect('blue:kelola_atraksi')
        else:
            pesan = "Atraksi berhasil disimpan"
            messages.success(request, pesan, extra_tags='atraksi')
    else:
        pesan = "Atraksi gagal diperbarui, pastikan data sudah benar" if nama_lama else "Atraksi gagal disimpan, pastikan data sudah benar"
        messages.error(request, pesan, extra_tags='atraksi')

    return redirect('blue:kelola_atraksi')

@admin_required
def delete_fasilitas(request):
    nama_fasilitas = request.POST.get('nama_fasilitas')
    jenis_fasilitas = request.POST.get('jenis_fasilitas')
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM SIZOPI.FASILITAS WHERE nama = %s
            """, [nama_fasilitas])
        messages.success(request, f"{jenis_fasilitas.capitalize()} berhasil dihapus", extra_tags=jenis_fasilitas.lower())
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan: {str(e)}", extra_tags=jenis_fasilitas.lower())
        
    if jenis_fasilitas == 'wahana':
        return redirect('blue:kelola_wahana')
    return redirect('blue:kelola_atraksi')

@admin_required
def kelola_pengunjung(request):
    return render(request, 'kelola_pengunjung.html')

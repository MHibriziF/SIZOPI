from django.shortcuts import render, redirect
from utils.db_connection import execute_query, execute_transaction
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

# Create your views here.
def reservasi(request):
    if not request.session.get('username'):
        return redirect('main:login')

    data_wahana = execute_query(query_fasilitas("wahana", "peraturan"));
    data_atraksi = execute_query(query_fasilitas("atraksi", "lokasi"));
    data_fasilitas = {
        'data_atraksi' : data_atraksi,
        'data_wahana'  : data_wahana
    }

    query = """
        SELECT 
            r.nama_fasilitas,
            a.lokasi,
            TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
            r.tanggal_kunjungan AS tanggal,
            r.jumlah_tiket AS tiket,
            r.status
        FROM RESERVASI r
        JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
        JOIN FASILITAS f ON a.nama_atraksi = f.nama
    """
    params = []
    if 'admin' in request.session.get("roles", []):
        query += " ORDER BY r.tanggal_kunjungan DESC;"
        roles = "admin"
    else:
        query += " WHERE r.username_p = %s ORDER BY r.tanggal_kunjungan DESC;"
        params = [request.session.get("username")]
        roles = "pengunjung"
        
    data_reservasi = execute_query(query, params)
    context = {
        'data_fasilitas' : data_fasilitas,
        'data_reservasi' : data_reservasi,
        'roles' : roles,
    }   
    return render(request, 'reservasi.html', context)

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
            w.peraturan
        FROM WAHANA w
        JOIN FASILITAS F ON w.nama_wahana = F.nama
    """
    wahana_raw = execute_query(query)
    data_wahana = []
    for row in wahana_raw:
        data_wahana.append({
            'nama_wahana': row['nama_wahana'],
            'kapasitas': row['kapasitas'],
            'jadwal': row['jadwal'],
            'peraturan': [p.strip() for p in row['peraturan'].split(';')],
        })

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
        queries = []
        params = []

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

        result = execute_transaction(queries, params)
        if result:
            messages.success(request, "Wahana berhasil diperbarui", extra_tags='wahana')
        else:
            messages.error(request, "Wahana gagal diperbarui, pastikan nama fasilitas unik", extra_tags='wahana')
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

        add_wahana = execute_transaction(queries, params)
        if add_wahana:
            messages.success(request, "Wahana berhasil disimpan", extra_tags='wahana')
        else:
            messages.error(request, "Wahana gagal disimpan, pastikan nama fasilitas unik", extra_tags='wahana')
    return redirect('blue:kelola_wahana')


@admin_required
def delete_wahana(request, nama_wahana):
    # Cek dulu apakah wahana ada
    check = execute_query("SELECT 1 FROM FASILITAS WHERE nama = %s", [nama_wahana])
    if not check:
        messages.error(request, "Wahana tidak ditemukan", extra_tags='wahana')
        return redirect('blue:kelola_wahana')

    # hapus wahana
    execute_query("DELETE FROM FASILITAS WHERE nama = %s", [nama_wahana])

    messages.success(request, "Wahana berhasil dihapus", extra_tags='wahana')
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
        JOIN PELATIH_HEWAN ph ON p.username = ph.username_lh;
    """)
 
    data_hewan = execute_query("""
        SELECT id, spesies, nama
        FROM HEWAN;
    """)

    context = {
        'data_atraksi' : data_atraksi,
        'data_hewan': data_hewan,
        'data_pelatih' : data_pelatih,
    }
    
    return render(request, 'atraksi.html', context)

def post_kelola_atraksi(request):
    nama_lama = request.POST.get('nama_atraksi_lama')  
    nama_atraksi = request.POST.get('nama_atraksi')
    lokasi = request.POST.get('lokasi')
    kapasitas = request.POST.get('kapasitas')
    jadwal = request.POST.get('jadwal')  
    pelatih_list = request.POST.getlist('pelatih')
    hewan_list = request.POST.getlist('hewan_terlibat')
    
    # cek kosong
    if not (nama_atraksi and lokasi and kapasitas and jadwal):
        messages.error(request, "Data atraksi tidak lengkap", extra_tags='atraksi')
        return redirect('blue:kelola_atraksi')
    
    tanggal_hari_ini = datetime.now().date()
    jadwal_str = f"{tanggal_hari_ini} {jadwal}"

    queries = []
    params = []

    if nama_lama:  # update atraksi 
        pass
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

        for username in pelatih_list:
            query_insert_jadwal = """
                INSERT INTO JADWAL_PENUGASAN (nama_atraksi, username_lh, tgl_penugasan) VALUES (%s, %s, %s)
            """
            queries.append(query_insert_jadwal)
            params.append((nama_atraksi, username, jadwal_str))

        for id_hewan in hewan_list:
            query_insert_hewan = """
                INSERT INTO BERPARTISIPASI (nama_fasilitas, id_hewan) VALUES (%s, %s)
            """
            queries.append(query_insert_hewan)
            params.append((nama_atraksi, id_hewan))

    result = execute_transaction(queries, params)
    if result:
        messages.success(request, "Atraksi berhasil disimpan", extra_tags='atraksi')
    else:
        messages.error(request, "Gagal menyimpan atraksi, cek kembali data input", extra_tags='atraksi')

    return redirect('blue:kelola_atraksi')

@admin_required
def delete_atraksi(request, nama_atraksi):
    # Cek dulu apakah wahana ada
    check = execute_query("SELECT 1 FROM FASILITAS WHERE nama = %s", [nama_atraksi])
    if not check:
        messages.error(request, "Atraksi tidak ditemukan", extra_tags='atraksi')
        return redirect('blue:kelola_atraksi')

    # hapus wahana
    execute_query("DELETE FROM FASILITAS WHERE nama = %s", [nama_atraksi])

    messages.success(request, "Atraksi berhasil dihapus", extra_tags='atraksi')
    return redirect('blue:kelola_atraksi')

@admin_required
def kelola_pengunjung(request):
    return render(request, 'kelola_pengunjung.html')

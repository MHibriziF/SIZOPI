from django.shortcuts import render, redirect
from utils.db_connection import execute_query, execute_transaction
from .decorators import admin_required
from datetime import date


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
                r.nama_atraksi,
                a.lokasi,
                TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
                r.tanggal_kunjungan AS tanggal,
                r.jumlah_tiket AS tiket,
                r.status
            FROM RESERVASI r
            JOIN ATRAKSI a ON r.nama_atraksi = a.nama_atraksi
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
        nama_wahana = request.POST.get('nama_wahana')
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        peraturan_list = request.POST.getlist('peraturan[]')
        peraturan_str = ';'.join([p.strip() for p in peraturan_list if p.strip()])

        queries = []
        params = []
        # Simpan ke FASILITAS
        query_fasilitas = """
            INSERT INTO FASILITAS (nama, kapasitas_max, jadwal)
            VALUES (%s, %s, %s)
        """
        queries.append(query_fasilitas)
        params.append((nama_wahana, kapasitas, f'2025-05-01 {jadwal}'))

        # Simpan ke WAHANA
        query_wahana = """
            INSERT INTO WAHANA (nama_wahana, peraturan)
            VALUES (%s, %s)
        """

        queries.append(query_wahana)
        params.append((nama_wahana, peraturan_str))

        add_wahana = execute_transaction(queries, params)
        if add_wahana:
            return redirect('blue:kelola_wahana')
        else:
            return redirect('blue:kelola_pengunjung')

    query = """
        SELECT 
            w.nama_wahana,
            f.kapasitas_max AS kapasitas,
            TO_CHAR(F.jadwal, 'HH24:MI:SS') AS jadwal,
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

@admin_required
def delete_wahana(request, nama_wahana):
    query = execute_query("DELETE FROM FASILITAS WHERE nama = %s", [nama_wahana])
    if query:
        pass
    else:
        pass
    return redirect('blue:kelola_wahana')

@admin_required
def kelola_atraksi(request):
    data_atraksi = execute_query("""
        SELECT 
            a.nama_atraksi,
            a.lokasi,
            f.kapasitas_max AS kapasitas,
            TO_CHAR(f.jadwal, 'HH24:MI:SS') AS jadwal,
            CONCAT(
                pg.nama_depan, 
                COALESCE(' ' || NULLIF(pg.nama_tengah, ''), ''), 
                ' ', 
                pg.nama_belakang
            ) AS pelatih,
            array_agg(DISTINCT h.spesies) AS hewan_terlibat
        FROM 
            ATRAKSI a
        JOIN 
            FASILITAS f ON a.nama_atraksi = f.nama
        LEFT JOIN 
            JADWAL_PENUGASAN p ON p.nama_atraksi = a.nama_atraksi
        LEFT JOIN 
            PELATIH_HEWAN ph ON p.username_lh = ph.username_lh
        LEFT JOIN 
            PENGGUNA pg ON ph.username_lh = pg.username
        LEFT JOIN 
            BERPARTISIPASI b ON b.nama_fasilitas = f.nama
        LEFT JOIN 
            HEWAN h ON b.id_hewan = h.id
        GROUP BY 
            a.nama_atraksi, a.lokasi, f.kapasitas_max, f.jadwal, pg.username
        HAVING 
            COUNT(h.nama) > 0 AND pg.username IS NOT NULL
        ORDER BY 
            a.nama_atraksi;
        """)
    # print(data_atraksi)
    data_pelatih = [
        {'nama_depan': 'Danang', 'nama_tengah': None, 'nama_belakang': 'Rajasa'},
        {'nama_depan': 'Faizah', 'nama_tengah': None, 'nama_belakang': 'Saputra'},
        {'nama_depan': 'Enteng', 'nama_tengah': None, 'nama_belakang': 'Sihotang'},
        {'nama_depan': 'Cici', 'nama_tengah': None, 'nama_belakang': 'Nasyiah'},
        {'nama_depan': 'Rahmat', 'nama_tengah': None, 'nama_belakang': 'Waskita'},
        {'nama_depan': 'Mulya', 'nama_tengah': None, 'nama_belakang': 'Ardianto'},
        {'nama_depan': 'Sadina', 'nama_tengah': None, 'nama_belakang': 'Pratiwi'},
        {'nama_depan': 'Oman', 'nama_tengah': 'Tedi', 'nama_belakang': 'Safitri'},
        {'nama_depan': 'Asmadi', 'nama_tengah': None, 'nama_belakang': 'Hasanah'},
    ]
    context = {
        'data_atraksi' : data_atraksi,
        'data_pelatih' : data_pelatih,
    }
    
    return render(request, 'atraksi.html', context)

@admin_required
def delete_atraksi(request, nama_atraksi):
    query = execute_query("DELETE FROM FASILITAS WHERE nama = %s", [nama_atraksi])
    if query:
        pass
    else:
        pass
    return redirect('blue:kelola_atraksi')

@admin_required
def kelola_pengunjung(request):
    return render(request, 'kelola_pengunjung.html')

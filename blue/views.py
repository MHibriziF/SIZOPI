from django.shortcuts import render, redirect
from utils.db_connection import execute_query
from datetime import date

# Create your views here.
def reservasi(request):
    if not request.session.get('username'):
        return redirect('main:login')

    if 'admin' not in request.session["roles"]:
        query = """
            SELECT 
                r.nama_atraksi,
                a.lokasi,
                f.jadwal::time AS jam,
                r.tanggal_kunjungan AS tanggal,
                r.jumlah_tiket AS tiket,
                r.status
            FROM RESERVASI r
            JOIN ATRAKSI a ON r.nama_atraksi = a.nama_atraksi
            JOIN FASILITAS f ON a.nama_atraksi = f.nama
            ORDER BY r.tanggal_kunjungan DESC;
        """
        data_reservasi = execute_query(query)
        context = {
            'data_reservasi' : data_reservasi,
            'roles' : 'pengunjung'
        }
    
    else:
        username = request.session.get("username")
        query = """
            SELECT 
                r.nama_atraksi,
                a.lokasi,
                f.jadwal::time AS jam,
                r.tanggal_kunjungan AS tanggal,
                r.jumlah_tiket AS tiket,
                r.status
            FROM RESERVASI r
            JOIN ATRAKSI a ON r.nama_atraksi = a.nama_atraksi
            JOIN FASILITAS f ON a.nama_atraksi = f.nama
            WHERE r.username_p = %s
            ORDER BY r.tanggal_kunjungan DESC;
        """
        
        data_reservasi = execute_query(query, [username])
        context = {
            'data_reservasi' : data_reservasi,
            'roles' : 'admin',
        }

    return render(request, 'reservasi.html', context)


def kelola_wahana(request):
    if not request.session.get('username'):
        return redirect('main:login')
    
    if 'admin' not in request.session["roles"] :
        return redirect('main:dashboard')
    
    # data_wahana = execute_query(
    #     "SELECT * FROM WAHANA"
    # )
    # print(data_wahana)

    # Hardcode dulu
    data_wahana = [{
        'nama_wahana': 'Petting Zoo Anak-Anak',
        'kapasitas' : 40,
        'jadwal' : '15:00:00',
        'peraturan' : ['Wajib cuci tangan sebelum/ setelah menyentuh hewan', 'Anak-anak harus didampingi orang tua.'],
    },
    {
        'nama_wahana': 'Safari Edukasi Reptil',
        'kapasitas' : 40,
        'jadwal' : '15:00:00',
        'peraturan' : ['Dilarang memberi makanan luar; Ikuti instruksi petugas', 'Jaga jarak aman dari pagar pengaman.'],
    }] 

    context = {
        'data_wahana' : data_wahana,
    }
    
    return render(request, 'wahana.html', context)

def kelola_atraksi(request):
    if not request.session.get('username'):
        return redirect('main:login')
    
    if 'admin' not in request.session["roles"] :
        return redirect('main:dashboard')
    
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
            FASILITAS f ON a.nama_atraksi = f.nama_atraksi
        LEFT JOIN 
            JADWAL_PENUGASAN p ON p.nama_atraksi = a.nama_atraksi
        LEFT JOIN 
            PELATIH_HEWAN ph ON p.username_lh = ph.username_lh
        LEFT JOIN 
            PENGGUNA pg ON ph.username_lh = pg.username
        LEFT JOIN 
            BERPARTISIPASI b ON b.nama_fasilitas = f.nama_atraksi
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

def kelola_pengunjung(request):
    if not request.session.get('username'):
        return redirect('main:login')
    
    if 'admin' not in request.session["roles"] :
        return redirect('main:dashboard')
    
    return render(request, 'kelola_pengunjung.html')


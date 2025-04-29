from django.shortcuts import render, redirect
from utils.db_connection import execute_query

# Create your views here.
def reservasi(request):

    # data_reservasi = execute_query(
    #     """
    #     """,
    # )

    if 'admin' not in request.session["roles"]:
        # Hardcode dulu
        data_reservasi = [{
            'nama_atraksi' : 'Ekshibisi Ular',
            'lokasi' : 'Galeri Reptil Utara',
            'jam' : '09:00',
            'tanggal': '2025-05-03',
            'tiket' : 5,
            'status' : 'Terjadwal',
        },
        {
            'nama_atraksi' : 'Pertunjukan Koala Cina',
            'lokasi' : 'Area Interaktif Barat',
            'jam' : '14:00',
            'tanggal': '2025-05-03',
            'tiket' : 5,
            'status' : 'Terjadwal',
        },
        {
            'nama_atraksi' : 'Pertunjukan Koala Cina',
            'lokasi' : 'Area Interaktif Barat',
            'jam' : '14:00',
            'tanggal': '2025-05-03',
            'tiket' : 3,
            'status' : 'Dibatalkan',
        }
        ]

        context = {
            'data_reservasi' : data_reservasi,
            'roles' : 'pengunjung'
        }
        return render(request, 'reservasi.html', context)
    else:
        # Hardcode dulu
        data_reservasi = [{
            'nama_atraksi' : 'Ekshibisi Ular',
            'lokasi' : 'Galeri Reptil Utara',
            'jam' : '09:00',
            'tanggal': '2025-05-03',
            'tiket' : 5,
            'status' : 'Terjadwal',
        },
        {
            'nama_atraksi' : 'Pertunjukan Koala Cina',
            'lokasi' : 'Area Interaktif Barat',
            'jam' : '14:00',
            'tanggal': '2025-05-03',
            'tiket' : 5,
            'status' : 'Terjadwal',
        },
        {
            'nama_atraksi' : 'Pertunjukan Koala Cina',
            'lokasi' : 'Area Interaktif Barat',
            'jam' : '14:00',
            'tanggal': '2025-05-03',
            'tiket' : 3,
            'status' : 'Dibatalkan',
        }
        ]

        context = {
            'data_reservasi' : data_reservasi,
            'roles' : 'admin',
        }
        return render(request, 'reservasi.html', context)


def kelola_wahana(request):
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
        'data_wahana' : data_wahana
    }
    
    return render(request, 'wahana.html', context)

def kelola_atraksi(request):
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
    print(data_atraksi)
    context = {
        'data_atraksi' : data_atraksi,
    }
    
    return render(request, 'atraksi.html', context)

def kelola_pengunjung(request):
    return render(request, 'kelola_pengunjung.html')


from django.shortcuts import render, redirect
from utils.db_connection import execute_query

# Create your views here.
def reservasi(request):

    # data_reservasi = execute_query(
    #     """
    #     """,
    # )

    return render(request, 'reservasi.html')

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
    
    # data_atraksi = execute_query(
    #     """
    #     """,
    # )
    # Hardcode dulu
    data_atraksi = [{
        'nama_atraksi': 'Safari Edukasi Reptil',
        'lokasi' : 'Zona Rawa',
        'kapasitas' : 30,
        'jadwal' : '10:00:00',
        'hewan_terlibat' : ['Buaya', 'Iguana'],
        'pelatih' : 'Danang Rajasa',
    },
    {
        'nama_atraksi': 'Ekshibisi Ular',
        'kapasitas' : 35,
        'lokasi' : 'Galeri Reptil Utara',
        'jadwal' : '09:00:00',
        'hewan_terlibat' : ['Ular'],
        'pelatih' : 'Cici Nasyiah',
    }] 

    context = {
        'data_atraksi' : data_atraksi,
    }
    
    return render(request, 'atraksi.html', context)

def kelola_pengunjung(request):
    return render(request, 'kelola_pengunjung.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import uuid
from green.views import get_hewan_by_id, get_all_hewan

def get_all_habitat_nama():
    """
    Fungsi untuk mengambil semua habitat dari database.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT nama FROM SIZOPI.HABITAT")
            habitat_list = [row[0] for row in cursor.fetchall()]
        print(f"Habitat List: {habitat_list}")  # Tambahkan log untuk debugging
        return habitat_list
    except Exception as e:
        print(f"Error saat mengambil data habitat: {str(e)}")
        return []

def hewan_list_view(request):
    """
    Fungsi untuk menampilkan daftar hewan dan menangani penambahan hewan baru.
    """
    # Ambil daftar habitat dari database
    habitat_list = get_all_habitat_nama()

    # Jika GET, ambil daftar hewan
    hewan_list = get_all_hewan()
    return render(request, 'manage_satwa/hewan_list.html', {
        'hewan_list': hewan_list,
        'habitat_list': habitat_list  # Kirim daftar habitat ke template
    })

def habitat_list_view(request):
    """
    Fungsi untuk menampilkan halaman daftar habitat.
    """
    return render(request, 'manage_habitat/habitat_list.html')

def tambah_hewan_view(request):
    """
    Fungsi untuk menambah hewan baru.
    """
    if request.method == 'POST':
        print("Fungsi tambah_hewan_view dipanggil")
        # Ambil data dari form
        nama = request.POST.get('nama')
        print(f"Nama hewan: {nama}")
        spesies = request.POST.get('spesies')
        asal_hewan = request.POST.get('asal_hewan')
        tanggal_lahir = request.POST.get('tanggal_lahir')
        status_kesehatan = request.POST.get('status_kesehatan')
        nama_habitat = request.POST.get('nama_habitat')
        url_foto = request.POST.get('url_foto')

        print(f"Data yang diterima: {nama}, {spesies}, {asal_hewan}, {tanggal_lahir}, {status_kesehatan}, {nama_habitat}, {url_foto}")

        try:
            # Periksa apakah data satwa sudah ada
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM SIZOPI.HEWAN
                    WHERE nama = %s AND spesies = %s AND asal_hewan = %s
                """, [nama, spesies, asal_hewan])
                result = cursor.fetchone()

            if result[0] > 0:
                # Jika data sudah ada, tampilkan pesan error
                messages.error(request, f"Data satwa atas nama “{nama}”, spesies “{spesies}”, dan berasal dari “{asal_hewan}” sudah terdaftar.")
                print(f"Data satwa sudah ada: {nama}, {spesies}, {asal_hewan}")
            else:
                # Jika data belum ada, simpan ke database
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO SIZOPI.HEWAN (id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        str(uuid.uuid4()),  # Generate UUID untuk ID
                        nama,
                        spesies,
                        asal_hewan,
                        tanggal_lahir,
                        status_kesehatan,
                        nama_habitat,
                        url_foto
                    ])
                messages.success(request, "Hewan berhasil ditambahkan!")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")

        # Redirect kembali ke halaman daftar hewan
        return redirect('yellow:hewan_list')

    # Jika bukan POST, redirect ke halaman daftar hewan
    return redirect('yellow:hewan_list')


def hapus_hewan_view(request, id):
    """
    Fungsi untuk menghapus hewan berdasarkan ID.
    """
    try:
        with connection.cursor() as cursor:
            # Hapus hewan berdasarkan ID
            cursor.execute("DELETE FROM SIZOPI.HEWAN WHERE id = %s", [id])
        messages.success(request, "Hewan berhasil dihapus!")
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus hewan: {str(e)}")

    # Redirect kembali ke halaman daftar hewan
    return redirect('yellow:hewan_list')
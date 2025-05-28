from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import uuid
from green.views import get_hewan_by_id, get_all_hewan


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

def habitat_list_view(request):
    """
    Fungsi untuk menampilkan halaman daftar habitat.
    """
    try:
        # Ambil semua data habitat dari database
        habitat_list = get_all_habitat()
        # print(habitat_list)
    except Exception as e:
        habitat_list = []
        print(f"Error saat mengambil data habitat: {str(e)}")
        messages.error(request, f"Terjadi kesalahan saat mengambil data habitat: {str(e)}")

    # Kirim data habitat ke template
    return render(request, 'manage_habitat/habitat_list.html', {
        'habitat_list': habitat_list
    })

def get_all_habitat():
    """
    Fungsi untuk mendapatkan semua data habitat dari database dalam format dictionary.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nama, luas_area, kapasitas, status
            FROM SIZOPI.HABITAT
            ORDER BY nama
        """)
        habitat_list = []
        for row in cursor.fetchall():
            habitat_list.append({
                'nama': row[0],
                'luas_area': row[1],
                'kapasitas': row[2],
                'status': row[3]
            })
        return habitat_list
    
def get_all_habitat_nama():
    """
    Fungsi untuk mengambil semua habitat dari database.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT nama FROM SIZOPI.HABITAT")
            habitat_list = [row[0] for row in cursor.fetchall()]
        # print(f"Habitat List: {habitat_list}")  # Tambahkan log untuk debugging
        return habitat_list
    except Exception as e:
        print(f"Error saat mengambil data habitat: {str(e)}")
        return []
    
def tambah_habitat_view(request):
    """
    Fungsi untuk menambah habitat baru.
    """
    if request.method == 'POST':
        print("Fungsi tambah_habitat_view dipanggil")
        # Ambil data dari form
        nama = request.POST.get('nama')
        luas_area = request.POST.get('luas_area')
        kapasitas = request.POST.get('kapasitas')
        status = request.POST.get('status')
        print(f"[DEBUG] Data diterima: nama={nama}, luas_area={luas_area}, kapasitas={kapasitas}, status={status}")
        try:
            # Periksa apakah habitat dengan nama yang sama sudah ada
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM SIZOPI.HABITAT
                    WHERE nama = %s
                """, [nama])
                result = cursor.fetchone()

            if result[0] > 0:
                # Jika habitat sudah ada, tampilkan pesan error
                messages.error(request, f"Habitat dengan nama '{nama}' sudah terdaftar.")
            else:
                # Jika habitat belum ada, tambahkan ke database
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO SIZOPI.HABITAT (nama, luas_area, kapasitas, status)
                        VALUES (%s, %s, %s, %s)
                    """, [nama, luas_area, kapasitas, status])
                messages.success(request, "Habitat berhasil ditambahkan!")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")

        # Redirect kembali ke halaman daftar habitat
        return redirect('yellow:habitat_list')

    # Jika bukan POST, redirect ke halaman daftar habitat
    return redirect('yellow:habitat_list')

def hapus_habitat_view(request, nama_habitat):
    """
    Fungsi untuk menghapus habitat berdasarkan nama habitat.
    """
    try:
        # Periksa apakah habitat dengan nama tersebut ada
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM SIZOPI.HABITAT
                WHERE nama = %s
            """, [nama_habitat])
            result = cursor.fetchone()

        if result[0] == 0:
            # Jika habitat tidak ditemukan, tampilkan pesan error
            messages.error(request, f"Habitat dengan nama '{nama_habitat}' tidak ditemukan.")
        else:
            # Hapus habitat dari database
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM SIZOPI.HABITAT
                    WHERE nama = %s
                """, [nama_habitat])
            messages.success(request, f"Habitat dengan nama '{nama_habitat}' berhasil dihapus.")
    except Exception as e:
        # Tangani error dan tampilkan pesan
        print(f"Error saat menghapus habitat: {str(e)}")
        messages.error(request, f"Terjadi kesalahan: {str(e)}")

    # Redirect kembali ke halaman daftar habitat
    return redirect('yellow:habitat_list')

def habitat_detail_view(request, nama_habitat):
    """
    Fungsi untuk menampilkan detail habitat beserta daftar hewan yang berada di habitat tersebut.
    """
    try:
        # Ambil detail habitat berdasarkan nama habitat
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nama, luas_area, kapasitas, status
                FROM SIZOPI.HABITAT
                WHERE nama = %s
            """, [nama_habitat])
            habitat = cursor.fetchone()

        # Jika habitat tidak ditemukan
        if not habitat:
            messages.error(request, f"Habitat dengan nama '{nama_habitat}' tidak ditemukan.")
            return redirect('yellow:habitat_list')

        # Ambil daftar hewan yang berada di habitat tersebut
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan
                FROM SIZOPI.HEWAN
                WHERE nama_habitat = %s
                ORDER BY nama
            """, [nama_habitat])
            hewan_list = cursor.fetchall()

        # Format data habitat dan hewan untuk dikirim ke template
        habitat_detail = {
            'nama': habitat[0],
            'luas_area': habitat[1],
            'kapasitas': habitat[2],
            'status': habitat[3],
        }
        hewan_list_formatted = [
            {
                'nama': hewan[0],
                'spesies': hewan[1],
                'asal_hewan': hewan[2],
                'tanggal_lahir': hewan[3],
                'status_kesehatan': hewan[4],
            }
            for hewan in hewan_list
        ]

        # Check if request accepts JSON
        if request.headers.get('Accept') == 'application/json':
            # Return JSON response
            return JsonResponse({
                'habitat': habitat_detail,
                'hewan_list': hewan_list_formatted,
            })
        else:
            # Return HTML response
            return render(request, 'manage_habitat/habitat_detail.html', {
                'habitat': habitat_detail,
                'hewan_list': hewan_list_formatted,
            })

    except Exception as e:
        # Tangani error dan tampilkan pesan
        print(f"Error saat mengambil detail habitat: {str(e)}")
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('yellow:habitat_list')
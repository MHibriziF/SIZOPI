from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import uuid
from green.views import get_hewan_by_id, get_all_hewan, is_dokter_hewan, is_penjaga_hewan

def is_staf_administrasi(request):
    """
    Mengecek apakah user adalah staf administrasi
    """
    if not request.session.get('username'):
        return False
    
    username = request.session.get('username')
    roles = request.session.get('roles', [])
    
    return 'admin' in roles

def dokter_penjaga_admin_required(view_func):
    """
    Decorator untuk view hewan yang bisa diakses oleh dokter hewan, penjaga hewan, dan staf administrasi
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (is_dokter_hewan(request) or is_penjaga_hewan(request) or is_staf_administrasi(request)):
            messages.error(request, "Anda tidak memiliki akses untuk halaman ini. Hanya dokter hewan, penjaga hewan, dan staf administrasi yang diizinkan.")
            return redirect('main:login')
        return view_func(request, *args, **kwargs)
    return wrapper

def penjaga_admin_required(view_func):
    """
    Decorator untuk view habitat yang bisa diakses oleh penjaga hewan dan staf administrasi
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (is_penjaga_hewan(request) or is_staf_administrasi(request)):
            messages.error(request, "Anda tidak memiliki akses untuk halaman ini. Hanya penjaga hewan dan staf administrasi yang diizinkan.")
            return redirect('main:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@dokter_penjaga_admin_required
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


@dokter_penjaga_admin_required
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
            # Langsung insert ke database, biarkan trigger yang mengecek duplikat
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
            error_message = str(e)
            print(f"Error dari database: {error_message}")
            
            # Cek apakah error berasal dari trigger duplikat
            if "sudah terdaftar" in error_message.lower() or "duplicate" in error_message.lower():
                # Ambil pesan error dari trigger dan tampilkan ke user
                messages.error(request, error_message)
            elif "sudah penuh" in error_message.lower() or "kapasitas" in error_message.lower():
                # Error dari trigger kapasitas habitat
                messages.error(request, error_message)
            else:
                # Error lainnya
                messages.error(request, f"Terjadi kesalahan: {error_message}")

        # Redirect kembali ke halaman daftar hewan
        return redirect('yellow:hewan_list')

    # Jika bukan POST, redirect ke halaman daftar hewan
    return redirect('yellow:hewan_list')

@dokter_penjaga_admin_required
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


@dokter_penjaga_admin_required
def edit_hewan_view(request, id):
    if request.method == 'POST':
        print("Fungsi edit_hewan_view dipanggil")
        
        # Ambil data dari form
        status_kesehatan = request.POST.get('status_kesehatan')
        nama_habitat = request.POST.get('nama_habitat')
        
        print(f"[DEBUG] Data diterima: id={id}, status_kesehatan={status_kesehatan}, nama_habitat={nama_habitat}")
        
        try:
            # Periksa apakah hewan dengan ID tersebut ada
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM SIZOPI.HEWAN
                    WHERE id = %s
                """, [id])
                result = cursor.fetchone()

            if result[0] == 0:
                # Jika hewan tidak ditemukan, tampilkan pesan error
                messages.error(request, f"Hewan dengan ID '{id}' tidak ditemukan.")
            else:
                # Validasi nama habitat jika diubah
                if nama_habitat:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT COUNT(*) FROM SIZOPI.HABITAT
                            WHERE nama = %s
                        """, [nama_habitat])
                        habitat_result = cursor.fetchone()
                    
                    if habitat_result[0] == 0:
                        messages.error(request, f"Habitat dengan nama '{nama_habitat}' tidak ditemukan.")
                        return redirect('yellow:hewan_list')
                
                # Clear any existing notices
                if hasattr(connection.connection, 'notices'):
                    connection.connection.notices.clear()
                
                # Update hewan di database - trigger akan otomatis mencatat riwayat
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE SIZOPI.HEWAN 
                        SET status_kesehatan = %s, nama_habitat = %s
                        WHERE id = %s
                    """, [status_kesehatan, nama_habitat, id])
                
                # Tangkap pesan NOTICE dari trigger
                trigger_notices = []
                if hasattr(connection.connection, 'notices'):
                    for notice in connection.connection.notices:
                        # Ambil pesan notice yang sebenarnya
                        if hasattr(notice, 'message_primary'):
                            notice_message = notice.message_primary
                        elif hasattr(notice, 'message'):
                            notice_message = notice.message
                        else:
                            notice_message = str(notice)
                        
                        # Hanya ambil notice yang mengandung 'SUKSES:'
                        if 'SUKSES:' in notice_message:
                            trigger_notices.append(notice_message)
                            print(f"[DEBUG] Trigger Notice: {notice_message}")
                
                combined_message = " ".join(trigger_notices)
                messages.error(request, combined_message)
                
        except Exception as e:
            error_message = str(e)
            print(f"Error dari database: {error_message}")
            
            # Tangkap pesan dari trigger atau error lainnya
            if "kapasitas" in error_message.lower() or "sudah penuh" in error_message.lower():
                # Error dari trigger kapasitas habitat
                messages.error(request, error_message)
            elif "tidak ditemukan" in error_message.lower():
                # Error validasi
                messages.error(request, error_message)
            else:
                # Error lainnya
                messages.error(request, f"Terjadi kesalahan saat memperbarui hewan: {error_message}")
            
            print(f"Error saat memperbarui hewan: {error_message}")

        # Redirect kembali ke halaman daftar hewan
        return redirect('yellow:hewan_list')

    elif request.method == 'GET':
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
                    FROM SIZOPI.HEWAN
                    WHERE id = %s
                """, [id])
                hewan = cursor.fetchone()

            if not hewan:
                messages.error(request, f"Hewan dengan ID '{id}' tidak ditemukan.")
                return redirect('yellow:hewan_list')

            hewan_data = {
                'id': hewan[0],
                'nama': hewan[1],
                'spesies': hewan[2],
                'asal_hewan': hewan[3],
                'tanggal_lahir': hewan[4],
                'status_kesehatan': hewan[5],
                'nama_habitat': hewan[6],
                'url_foto': hewan[7],
            }

            # Ambil daftar habitat untuk dropdown
            habitat_list = get_all_habitat_nama()

            # Check if request is AJAX (for modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'hewan': hewan_data,
                    'habitat_list': habitat_list
                })
            else:
                # Render halaman edit hewan
                return render(request, 'manage_satwa/edit_hewan.html', {
                    'hewan': hewan_data,
                    'habitat_list': habitat_list
                })
                
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat mengambil data hewan: {str(e)}")
            print(f"Error saat mengambil data hewan: {str(e)}")
            return redirect('yellow:hewan_list')

    # Jika method lain, redirect ke halaman daftar hewan
    return redirect('yellow:hewan_list')


@dokter_penjaga_admin_required
def riwayat_hewan_view(request, id):
    """
    Fungsi untuk menampilkan riwayat perubahan hewan berdasarkan ID.
    """
    try:
        # Ambil data hewan terlebih dahulu
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, nama, spesies, asal_hewan
                FROM SIZOPI.HEWAN
                WHERE id = %s
            """, [id])
            hewan = cursor.fetchone()

        if not hewan:
            messages.error(request, f"Hewan dengan ID '{id}' tidak ditemukan.")
            return redirect('yellow:hewan_list')

        # Ambil riwayat perubahan hewan
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    r.id,
                    r.kolom_perubahan,
                    r.nilai_sebelum,
                    r.nilai_sesudah,
                    r.dibuat_pada
                FROM SIZOPI.RIWAYAT_SATWA r
                WHERE r.satwa_id = %s
                ORDER BY r.dibuat_pada DESC
            """, [id])
            riwayat_list = cursor.fetchall()

        # Format data hewan
        hewan_data = {
            'id': hewan[0],
            'nama': hewan[1],
            'spesies': hewan[2],
            'asal_hewan': hewan[3]
        }

        # Format data riwayat
        riwayat_formatted = []
        for riwayat in riwayat_list:
            # Format nama kolom menjadi lebih readable
            kolom_display = {
                'STATUS_KESEHATAN': 'Status Kesehatan',
                'NAMA_HABITAT': 'Habitat'
            }.get(riwayat[1], riwayat[1])

            riwayat_formatted.append({
                'id': riwayat[0],
                'kolom_perubahan': riwayat[1],
                'kolom_display': kolom_display,
                'nilai_sebelum': riwayat[2] if riwayat[2] else '-',
                'nilai_sesudah': riwayat[3] if riwayat[3] else '-',
                'dibuat_pada': riwayat[4]
            })

        # Check if request is AJAX (for modal)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'hewan': hewan_data,
                'riwayat_list': riwayat_formatted
            })
        else:
            # Render halaman riwayat hewan
            return render(request, 'manage_satwa/riwayat_hewan.html', {
                'hewan': hewan_data,
                'riwayat_list': riwayat_formatted
            })

    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat mengambil riwayat hewan: {str(e)}")
        print(f"Error saat mengambil riwayat hewan: {str(e)}")
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': str(e)}, status=500)
        return redirect('yellow:hewan_list')


@penjaga_admin_required
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

  
@penjaga_admin_required  
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

    
@penjaga_admin_required
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

  
@penjaga_admin_required  
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

  
@penjaga_admin_required      
def edit_habitat_view(request, nama_habitat):
    """
    Fungsi untuk mengedit habitat berdasarkan nama habitat.
    Hanya dapat mengedit status lingkungan dan kapasitas.
    """
    if request.method == 'POST':
        print("Fungsi edit_habitat_view dipanggil")
        
        # Ambil data dari form
        kapasitas = request.POST.get('kapasitas')
        status = request.POST.get('status')
        
        print(f"[DEBUG] Data diterima: nama_habitat={nama_habitat}, kapasitas={kapasitas}, status={status}")
        
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
                # Update habitat di database
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE SIZOPI.HABITAT 
                        SET kapasitas = %s, status = %s
                        WHERE nama = %s
                    """, [kapasitas, status, nama_habitat])
                messages.success(request, f"Habitat '{nama_habitat}' berhasil diperbarui!")
                
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat memperbarui habitat: {str(e)}")
            print(f"Error saat memperbarui habitat: {str(e)}")

        # Redirect kembali ke halaman daftar habitat
        return redirect('yellow:habitat_list')

    elif request.method == 'GET':
        # Jika GET request, ambil data habitat untuk ditampilkan di form
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT nama, luas_area, kapasitas, status
                    FROM SIZOPI.HABITAT
                    WHERE nama = %s
                """, [nama_habitat])
                habitat = cursor.fetchone()

            if not habitat:
                messages.error(request, f"Habitat dengan nama '{nama_habitat}' tidak ditemukan.")
                return redirect('yellow:habitat_list')

            habitat_data = {
                'nama': habitat[0],
                'luas_area': habitat[1],
                'kapasitas': habitat[2],
                'status': habitat[3],
            }

            # Check if request is AJAX (for modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'habitat': habitat_data
                })
            else:
                # Render halaman edit habitat
                return render(request, 'manage_habitat/edit_habitat.html', {
                    'habitat': habitat_data
                })
                
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat mengambil data habitat: {str(e)}")
            print(f"Error saat mengambil data habitat: {str(e)}")
            return redirect('yellow:habitat_list')

    # Jika method lain, redirect ke halaman daftar habitat
    return redirect('yellow:habitat_list')
import uuid
import psycopg2
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse

def is_dokter_hewan(request):
    if not request.session.get('username'):
        return False
    
    username = request.session.get('username')
    roles = request.session.get('roles', [])
    
    return 'dokter' in roles

def is_penjaga_hewan(request):
    if not request.session.get('username'):
        return False
    
    username = request.session.get('username')
    roles = request.session.get('roles', [])
    
    return 'penjaga' in roles

def dokter_hewan_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not is_dokter_hewan(request):
            messages.error(request, "Anda tidak memiliki akses untuk halaman ini. Hanya dokter hewan yang diizinkan.")
            return redirect('main:login')
        return view_func(request, *args, **kwargs)
    return wrapper

def penjaga_hewan_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not is_penjaga_hewan(request):
            messages.error(request, "Anda tidak memiliki akses untuk halaman ini. Hanya penjaga hewan yang diizinkan.")
            return redirect('main:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_hewan_by_id(id_hewan):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM SIZOPI.HEWAN
            WHERE id = %s
        """, [id_hewan])
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'nama': row[1],
                'spesies': row[2],
                'asal_hewan': row[3],
                'tanggal_lahir': row[4],
                'status_kesehatan': row[5],
                'nama_habitat': row[6],
                'url_foto': row[7]
            }
        return None

def get_all_hewan():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM SIZOPI.HEWAN
            ORDER BY nama
        """)
        hewan_list = []
        for row in cursor.fetchall():
            hewan_list.append({
                'id': row[0],
                'nama': row[1],
                'spesies': row[2],
                'asal_hewan': row[3],
                'tanggal_lahir': row[4],
                'status_kesehatan': row[5],
                'nama_habitat': row[6],
                'url_foto': row[7]
            })
        return hewan_list


@dokter_hewan_required
def rekam_medis_list(request):
    id_hewan = request.GET.get('id_hewan')
    
    if not id_hewan:
        hewan_list = get_all_hewan()
        return render(request, 'rekam_medis/hewan_list.html', {'hewan_list': hewan_list})
    
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:rekam_medis_list')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cm.tanggal_pemeriksaan, p.nama_depan || ' ' || p.nama_belakang as nama_dokter, 
                   cm.status_kesehatan, cm.diagnosis, cm.pengobatan, cm.catatan_tindak_lanjut
            FROM SIZOPI.CATATAN_MEDIS cm
            JOIN SIZOPI.PENGGUNA p ON cm.username_dh = p.username
            WHERE cm.id_hewan = %s
            ORDER BY cm.tanggal_pemeriksaan DESC
        """, [id_hewan])
        
        rekam_medis_list = []
        for row in cursor.fetchall():
            rekam_medis_list.append({
                'tanggal_pemeriksaan': row[0],
                'nama_dokter': row[1],
                'status_kesehatan': row[2],
                'diagnosis': row[3],
                'pengobatan': row[4],
                'catatan_tindak_lanjut': row[5]
            })
    
    context = {
        'hewan': hewan,
        'rekam_medis_list': rekam_medis_list
    }
    
    return render(request, 'rekam_medis/rekam_medis_list.html', context)

@dokter_hewan_required
def rekam_medis_create(request, id_hewan):
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:rekam_medis_list')
    
    if request.method == 'POST':
        tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
        status_kesehatan = request.POST.get('status_kesehatan')
        diagnosis = request.POST.get('diagnosis')
        pengobatan = request.POST.get('pengobatan')
        
        if not tanggal_pemeriksaan:
            messages.error(request, "Tanggal pemeriksaan harus diisi")
            return render(request, 'rekam_medis/rekam_medis_form.html', {'hewan': hewan})
        
        if status_kesehatan == 'Sakit' and (not diagnosis or not pengobatan):
            messages.error(request, "Diagnosis dan pengobatan harus diisi untuk status sakit")
            return render(request, 'rekam_medis/rekam_medis_form.html', {'hewan': hewan})
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM SIZOPI.CATATAN_MEDIS 
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [id_hewan, tanggal_pemeriksaan])
                
                if cursor.fetchone()[0] > 0:
                    messages.error(request, "Rekam medis untuk tanggal ini sudah ada")
                    return render(request, 'rekam_medis/rekam_medis_form.html', {'hewan': hewan})
                
                cursor.execute("""
                    INSERT INTO SIZOPI.CATATAN_MEDIS (id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut)
                    VALUES (%s, %s, %s, %s, %s, %s, NULL)
                """, [id_hewan, request.session.get('username'), tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan])
                
                cursor.execute("""
                    UPDATE SIZOPI.HEWAN
                    SET status_kesehatan = %s
                    WHERE id = %s
                """, [status_kesehatan, id_hewan])
                
                messages.success(request, "Rekam medis berhasil ditambahkan")
                return redirect('green:rekam_medis_list')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return render(request, 'rekam_medis/rekam_medis_form.html', {'hewan': hewan})

@dokter_hewan_required
def rekam_medis_update(request, id_hewan, tanggal):
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:rekam_medis_list')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut
            FROM SIZOPI.CATATAN_MEDIS
            WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
        """, [id_hewan, tanggal])
        
        row = cursor.fetchone()
        if not row:
            messages.error(request, "Rekam medis tidak ditemukan")
            return redirect('green:rekam_medis_list')
        
        rekam_medis = {
            'id_hewan': row[0],
            'username_dh': row[1],
            'tanggal_pemeriksaan': row[2],
            'diagnosis': row[3],
            'pengobatan': row[4],
            'status_kesehatan': row[5],
            'catatan_tindak_lanjut': row[6]
        }
    
    if rekam_medis['status_kesehatan'] != 'Sakit':
        messages.error(request, "Hanya rekam medis dengan status Sakit yang dapat diedit")
        return redirect('green:rekam_medis_list')
    
    if request.method == 'POST':
        catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut')
        diagnosis_baru = request.POST.get('diagnosis_baru')
        pengobatan_baru = request.POST.get('pengobatan_baru')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.CATATAN_MEDIS
                    SET diagnosis = %s, pengobatan = %s, catatan_tindak_lanjut = %s
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [diagnosis_baru, pengobatan_baru, catatan_tindak_lanjut, id_hewan, tanggal])
                
                messages.success(request, "Rekam medis berhasil diperbarui")
                return redirect('green:rekam_medis_list')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    context = {
        'hewan': hewan,
        'rekam_medis': rekam_medis
    }
    
    return render(request, 'rekam_medis/rekam_medis_edit_form.html', context)

@dokter_hewan_required
def rekam_medis_delete(request, id_hewan, tanggal):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                # Hapus rekam medis
                cursor.execute("""
                    DELETE FROM SIZOPI.CATATAN_MEDIS
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [id_hewan, tanggal])
                
                messages.success(request, "Rekam medis berhasil dihapus")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return redirect('green:rekam_medis_list')


@dokter_hewan_required
def jadwal_pemeriksaan_list(request):
    id_hewan = request.GET.get('id_hewan')
    
    if not id_hewan:
        hewan_list = get_all_hewan()
        return render(request, 'jadwal_pemeriksaan/hewan_list.html', {'hewan_list': hewan_list})
    
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:jadwal_pemeriksaan_list')

    frekuensi = None
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT freq_pemeriksaan_rutin FROM SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
            WHERE id_hewan = %s
            LIMIT 1
        """, [id_hewan])
        
        result = cursor.fetchone()
        if result:
            frekuensi = result[0]
    
    # Ambil jadwal pemeriksaan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tgl_pemeriksaan_selanjutnya
            FROM SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
            WHERE id_hewan = %s
            ORDER BY tgl_pemeriksaan_selanjutnya
        """, [id_hewan])
        
        jadwal_list = []
        for row in cursor.fetchall():
            jadwal_list.append({
                'tanggal': row[0]
            })
    
    context = {
        'hewan': hewan,
        'jadwal_list': jadwal_list,
        'frekuensi': frekuensi,
        'today': datetime.now().date()
    }
    
    return render(request, 'jadwal_pemeriksaan/jadwal_list.html', context)

@dokter_hewan_required
def jadwal_pemeriksaan_create(request, id_hewan):
    # Ambil data hewan
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:jadwal_pemeriksaan_list')
    
    # Ambil frekuensi pemeriksaan yang ada (jika ada)
    frekuensi = 3  # Default: 3 bulan sekali
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT freq_pemeriksaan_rutin FROM SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
            WHERE id_hewan = %s
            LIMIT 1
        """, [id_hewan])
        
        result = cursor.fetchone()
        if result:
            frekuensi = result[0]
    
    if request.method == 'POST':
        tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
        
        if not tanggal_pemeriksaan:
            messages.error(request, "Tanggal pemeriksaan harus diisi")
            return render(request, 'jadwal_pemeriksaan/jadwal_form.html', {'hewan': hewan})
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN 
                    WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
                """, [id_hewan, tanggal_pemeriksaan])
                
                if cursor.fetchone()[0] > 0:
                    messages.error(request, "Jadwal pemeriksaan untuk tanggal ini sudah ada")
                    return render(request, 'jadwal_pemeriksaan/jadwal_form.html', {'hewan': hewan})
                
                cursor.execute("""
                    INSERT INTO SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
                    VALUES (%s, %s, %s)
                """, [id_hewan, tanggal_pemeriksaan, frekuensi])
                
                messages.success(request, "Jadwal pemeriksaan berhasil ditambahkan")
                return redirect('green:jadwal_pemeriksaan_list')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return render(request, 'jadwal_pemeriksaan/jadwal_form.html', {'hewan': hewan})


@penjaga_hewan_required
def pemberian_pakan_list(request):
    id_hewan = request.GET.get('id_hewan')
    
    if not id_hewan:
        hewan_list = get_all_hewan()
        return render(request, 'pemberian_pakan/hewan_list.html', {'hewan_list': hewan_list})
    
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:pemberian_pakan_list')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT jenis, jumlah, jadwal, status
            FROM SIZOPI.PAKAN
            WHERE id_hewan = %s
            ORDER BY jadwal
        """, [id_hewan])
        
        pakan_list = []
        for row in cursor.fetchall():
            pakan_list.append({
                'jenis': row[0],
                'jumlah': row[1],
                'jadwal': row[2],
                'status': row[3]
            })
    
    context = {
        'hewan': hewan,
        'pakan_list': pakan_list
    }
    
    return render(request, 'pemberian_pakan/pakan_list.html', context)

@penjaga_hewan_required
def riwayat_pemberian_pakan(request):
    username = request.session.get('username')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.nama, h.spesies, h.asal_hewan, h.tanggal_lahir, h.nama_habitat, h.status_kesehatan,
                   p.jenis, p.jumlah, p.jadwal
            FROM SIZOPI.MEMBERI m
            JOIN SIZOPI.HEWAN h ON m.id_hewan = h.id
            JOIN SIZOPI.PAKAN p ON m.id_hewan = p.id_hewan AND m.jadwal = p.jadwal
            WHERE m.username_jh = %s
            ORDER BY p.jadwal DESC
        """, [username])
        
        riwayat_list = []
        for row in cursor.fetchall():
            riwayat_list.append({
                'nama': row[0],
                'spesies': row[1],
                'asal_hewan': row[2],
                'tanggal_lahir': row[3],
                'habitat': row[4],
                'status_kesehatan': row[5],
                'jenis_pakan': row[6],
                'jumlah_pakan': row[7],
                'jadwal': row[8]
            })
    
    return render(request, 'pemberian_pakan/riwayat_pakan.html', {'riwayat_list': riwayat_list})

@penjaga_hewan_required
def pemberian_pakan_create(request, id_hewan):
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:pemberian_pakan_list')
    
    if request.method == 'POST':
        jenis_pakan = request.POST.get('jenis_pakan')
        jumlah_pakan = request.POST.get('jumlah_pakan')
        jadwal = request.POST.get('jadwal')
        
        if not jenis_pakan or not jumlah_pakan or not jadwal:
            messages.error(request, "Semua field harus diisi")
            return render(request, 'pemberian_pakan/pakan_form.html', {'hewan': hewan})
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM SIZOPI.PAKAN 
                    WHERE id_hewan = %s AND jadwal = %s
                """, [id_hewan, jadwal])
                
                if cursor.fetchone()[0] > 0:
                    messages.error(request, "Jadwal pemberian pakan untuk waktu ini sudah ada")
                    return render(request, 'pemberian_pakan/pakan_form.html', {'hewan': hewan})
                
                cursor.execute("""
                    INSERT INTO SIZOPI.PAKAN (id_hewan, jadwal, jenis, jumlah, status)
                    VALUES (%s, %s, %s, %s, 'Menunggu Pemberian')
                """, [id_hewan, jadwal, jenis_pakan, jumlah_pakan])
                
                messages.success(request, "Jadwal pemberian pakan berhasil ditambahkan")
                return redirect('green:pemberian_pakan_list')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return render(request, 'pemberian_pakan/pakan_form.html', {'hewan': hewan})

@penjaga_hewan_required
def pemberian_pakan_update(request, id_hewan, jadwal):
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:pemberian_pakan_list')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT jenis, jumlah, jadwal, status
            FROM SIZOPI.PAKAN
            WHERE id_hewan = %s AND jadwal = %s
        """, [id_hewan, jadwal])
        
        row = cursor.fetchone()
        if not row:
            messages.error(request, "Jadwal pemberian pakan tidak ditemukan")
            return redirect('green:pemberian_pakan_list')
        
        pakan = {
            'jenis': row[0],
            'jumlah': row[1],
            'jadwal': row[2],
            'status': row[3]
        }
    
    if request.method == 'POST':
        jenis_pakan_baru = request.POST.get('jenis_pakan_baru')
        jumlah_pakan_baru = request.POST.get('jumlah_pakan_baru')
        jadwal_baru = request.POST.get('jadwal_baru')
        
        if not jenis_pakan_baru or not jumlah_pakan_baru or not jadwal_baru:
            messages.error(request, "Semua field harus diisi")
            return render(request, 'pemberian_pakan/pakan_edit_form.html', {'hewan': hewan, 'pakan': pakan})
        
        try:
            with connection.cursor() as cursor:
                if jadwal != jadwal_baru:
                    cursor.execute("""
                        SELECT COUNT(*) FROM SIZOPI.PAKAN 
                        WHERE id_hewan = %s AND jadwal = %s
                    """, [id_hewan, jadwal_baru])
                    
                    if cursor.fetchone()[0] > 0:
                        messages.error(request, "Jadwal pemberian pakan untuk waktu ini sudah ada")
                        return render(request, 'pemberian_pakan/pakan_edit_form.html', {'hewan': hewan, 'pakan': pakan})
                
                cursor.execute("""
                    UPDATE SIZOPI.PAKAN
                    SET jenis = %s, jumlah = %s, jadwal = %s
                    WHERE id_hewan = %s AND jadwal = %s
                """, [jenis_pakan_baru, jumlah_pakan_baru, jadwal_baru, id_hewan, jadwal])
                
                messages.success(request, "Jadwal pemberian pakan berhasil diperbarui")
                return redirect('green:pemberian_pakan_list')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    context = {
        'hewan': hewan,
        'pakan': pakan
    }
    
    return render(request, 'pemberian_pakan/pakan_edit_form.html', context)

@penjaga_hewan_required
def pemberian_pakan_delete(request, id_hewan, jadwal):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM SIZOPI.PAKAN
                    WHERE id_hewan = %s AND jadwal = %s
                """, [id_hewan, jadwal])
                
                messages.success(request, "Jadwal pemberian pakan berhasil dihapus")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return redirect('green:pemberian_pakan_list')

@penjaga_hewan_required
def pemberian_pakan_beri(request, id_hewan, jadwal):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.PAKAN
                    SET status = 'Selesai Diberikan'
                    WHERE id_hewan = %s AND jadwal = %s AND status = 'Menunggu Pemberian'
                """, [id_hewan, jadwal])
                
                cursor.execute("""
                    INSERT INTO SIZOPI.MEMBERI (id_hewan, jadwal, username_jh)
                    VALUES (%s, %s, %s)
                """, [id_hewan, jadwal, request.session.get('username')])
                
                messages.success(request, "Pakan berhasil diberikan")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return redirect('green:pemberian_pakan_list')
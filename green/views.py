import uuid
import psycopg2
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from urllib.parse import unquote

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
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM get_medical_records(%s)
            """, [id_hewan])
            
            rekam_medis_list = []
            for row in cursor.fetchall():
                rekam_medis_list.append({
                    'tanggal_pemeriksaan': row[2],
                    'nama_dokter': row[3],
                    'status_kesehatan': row[4],
                    'diagnosis': row[5],
                    'pengobatan': row[6],
                    'catatan_tindak_lanjut': row[7]
                })
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat mengambil data: {str(e)}")
        rekam_medis_list = []
    
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
        catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut')
        
        if not tanggal_pemeriksaan:
            messages.error(request, "Tanggal pemeriksaan harus diisi")
            return render(request, 'rekam_medis/rekam_medis_form.html', {'hewan': hewan})
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET client_min_messages TO NOTICE")
                
                cursor.execute("""
                    SELECT success, message FROM add_medical_record(
                        %s, %s, %s, %s, %s, %s, %s
                    )
                """, [
                    id_hewan, 
                    request.session.get('username'), 
                    tanggal_pemeriksaan, 
                    diagnosis, 
                    pengobatan, 
                    status_kesehatan,
                    catatan_tindak_lanjut
                ])
                
                result = cursor.fetchone()
                if result and result[0]: 
                    success_message = result[1]
                    messages.success(request, success_message)
                    
                    if status_kesehatan == 'Sakit':
                        trigger_message = f'SUKSES: Jadwal pemeriksaan hewan "{hewan["nama"]}" telah diperbarui karena status kesehatan "Sakit".'
                        messages.success(request, trigger_message)
                    
                    return redirect(f'{reverse("green:rekam_medis_list")}?id_hewan={id_hewan}')
                else:
                    error_message = result[1] if result else "Terjadi kesalahan saat menambah rekam medis"
                    messages.error(request, error_message)
                    
        except Exception as e:
            error_message = str(e)
            if "ERROR:" in error_message:
                error_message = error_message.split("ERROR:")[-1].strip()
            messages.error(request, error_message)
    
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

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM get_medical_schedules(%s)
            """, [id_hewan])
            
            jadwal_list = []
            frekuensi = None
            for row in cursor.fetchall():
                jadwal_list.append({
                    'tanggal': row[2],
                    'days_until': row[4]
                })
                if frekuensi is None:
                    frekuensi = row[3]
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat mengambil data: {str(e)}")
        jadwal_list = []
        frekuensi = None
    
    context = {
        'hewan': hewan,
        'jadwal_list': jadwal_list,
        'frekuensi': frekuensi,
        'today': datetime.now().date()
    }
    
    return render(request, 'jadwal_pemeriksaan/jadwal_list.html', context)

@dokter_hewan_required
def jadwal_pemeriksaan_create(request, id_hewan):
    hewan = get_hewan_by_id(id_hewan)
    if not hewan:
        messages.error(request, "Hewan tidak ditemukan")
        return redirect('green:jadwal_pemeriksaan_list')
    
    if request.method == 'POST':
        tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
        frekuensi_bulan = request.POST.get('frekuensi_bulan', 3)
        
        if not tanggal_pemeriksaan:
            messages.error(request, "Tanggal pemeriksaan harus diisi")
            return render(request, 'jadwal_pemeriksaan/jadwal_form.html', {'hewan': hewan})
        
        try:
            frekuensi_bulan = int(frekuensi_bulan)
        except (ValueError, TypeError):
            frekuensi_bulan = 3 
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET client_min_messages TO NOTICE")
                
                cursor.execute("""
                    SELECT success, message FROM add_medical_schedule(%s, %s, %s)
                """, [id_hewan, tanggal_pemeriksaan, frekuensi_bulan])
                
                result = cursor.fetchone()
                if result and result[0]:  
                    success_message = result[1]
                    messages.success(request, success_message)

                    trigger_message = f'SUKSES: Jadwal pemeriksaan rutin hewan "{hewan["nama"]}" telah ditambahkan sesuai frekuensi.'
                    messages.success(request, trigger_message)
                    
                    return redirect(f'{reverse("green:jadwal_pemeriksaan_list")}?id_hewan={id_hewan}')
                else:
                    error_message = result[1] if result else "Terjadi kesalahan saat menambah jadwal"
                    messages.error(request, error_message)
                    
        except Exception as e:
            error_message = str(e)
            if "ERROR:" in error_message:
                error_message = error_message.split("ERROR:")[-1].strip()
            messages.error(request, error_message)
    
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
    jadwal = unquote(jadwal)
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
    jadwal = unquote(jadwal)
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
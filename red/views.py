from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from utils.db_connection import execute_query, execute_transaction
import uuid, datetime
# from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.dateparse import parse_date

# Helper Functions
def is_admin(request):
    return 'admin' in request.session.get('roles', [])

def is_pengunjung(request):
    return 'pengunjung' in request.session.get('roles', [])

def ensure_adopter(request):
    username = request.session['username']
    row = execute_query(
      "SELECT id_adopter FROM ADOPTER WHERE username_adopter = %s",
      (username,)
    )
    if row:
        return row[0]['id_adopter']
    new_id = str(uuid.uuid4())
    execute_query(
      "INSERT INTO ADOPTER(username_adopter,id_adopter,total_kontribusi) VALUES(%s,%s,0)",
      (username,new_id)
    )
    return new_id

@require_http_methods(["GET"])
def api_check_user(request):
    username = request.GET.get('username', '')
    exists = bool(execute_query(
        "SELECT 1 FROM PENGUNJUNG WHERE username_p = %s",
        (username,)
    ))
    return JsonResponse({'exists': exists})

@require_http_methods(["GET"])
def api_get_adopter(request):
    username = request.GET.get("username", "").strip()
    if not username:
        return JsonResponse({"exists": False}, status=400)

    row = execute_query(
      """
      SELECT a.id_adopter,
             p.alamat,
             u.no_telepon
      FROM ADOPTER a
      JOIN PENGUNJUNG p ON a.username_adopter = p.username_p
      JOIN PENGGUNA  u ON a.username_adopter = u.username
      WHERE a.username_adopter = %s
      """,
      (username,)
    )
    if not row:
        return JsonResponse({"exists": False})
    data = row[0]
    return JsonResponse({
      "exists": True,
      "id_adopter": str(data["id_adopter"]),
      "alamat": data["alamat"],
      "no_telepon": data["no_telepon"],
    })

def ensure_adopter(request):
    username = request.session['username']
    row = execute_query(
        "SELECT id_adopter FROM ADOPTER WHERE username_adopter = %s",
        (username,)
    )
    if row:
        return row[0]['id_adopter']
    new_id = str(uuid.uuid4())
    execute_query(
        "INSERT INTO ADOPTER(username_adopter, id_adopter, total_kontribusi) "
        "VALUES (%s, %s, 0)",
        (username, new_id)
    )
    return new_id

# List Adopter (READ)
@require_http_methods(["GET"])
def list_adopters(request):
    if not is_admin(request):
        return redirect('main:login')

    # ambil snapshot Top-5
    top5 = execute_query("""
       SELECT rank, nama_adopter, total
       FROM top5_adopter
       ORDER BY rank
    """, ())

    # 2) Daftar Individu: sum total lunas, flag aktif
    individuals = execute_query("""
        SELECT
          i.nama               AS nama_adopter,
          a.id_adopter,
          COALESCE(SUM(o.kontribusi_finansial),0) AS total_kontribusi,
          EXISTS (
            SELECT 1
            FROM ADOPSI ad
            WHERE ad.id_adopter = a.id_adopter
              AND ad.status_pembayaran = 'lunas'
              AND ad.tgl_mulai_adopsi <= CURRENT_DATE
              AND ad.tgl_berhenti_adopsi >= CURRENT_DATE
          ) AS is_active
        FROM ADOPTER a
        JOIN INDIVIDU i  ON a.id_adopter = i.id_adopter
        LEFT JOIN ADOPSI o
          ON a.id_adopter = o.id_adopter
         AND o.status_pembayaran = 'lunas'
        GROUP BY i.nama, a.id_adopter
        ORDER BY i.nama
    """, ())

    # 3) Daftar Organisasi: sum total lunas, flag aktif
    organizations = execute_query("""
        SELECT
          org.nama_organisasi  AS nama_adopter,
          a.id_adopter,
          COALESCE(SUM(o.kontribusi_finansial),0) AS total_kontribusi,
          EXISTS (
            SELECT 1
            FROM ADOPSI ad
            WHERE ad.id_adopter = a.id_adopter
              AND ad.status_pembayaran = 'lunas'
              AND ad.tgl_mulai_adopsi <= CURRENT_DATE
              AND ad.tgl_berhenti_adopsi >= CURRENT_DATE
          ) AS is_active
        FROM ADOPTER a
        JOIN ORGANISASI org ON a.id_adopter = org.id_adopter
        LEFT JOIN ADOPSI o
          ON a.id_adopter = o.id_adopter
         AND o.status_pembayaran = 'lunas'
        GROUP BY org.nama_organisasi, a.id_adopter
        ORDER BY org.nama_organisasi
    """, ())

    return render(request, 'adopter_list.html', {
        'top_adopters':   top5,
        'individuals':    individuals,
        'organizations':  organizations,
    })

# Registrasi Adopter (CREATE)
@require_http_methods(["GET", "POST"])
def register_adopter(request):
    if not is_admin(request):
        return redirect('main:login')

    if request.method == "POST":
        username = request.POST.get("username")
        tipe     = request.POST.get("tipe")
        new_id   = str(uuid.uuid4())

        sqls, params = [], []
        sqls.append("INSERT INTO ADOPTER (username_adopter, id_adopter, total_kontribusi) VALUES (%s, %s, 0)")
        params.append((username, new_id))

        if tipe == "Individu":
            nik  = request.POST.get("nik")
            nama = request.POST.get("nama_lengkap")
            if not nik or not nama:
                messages.error(request, "NIK dan nama wajib diisi untuk individu.")
                return redirect('adopsi:register_adopter')

            sqls.append("INSERT INTO INDIVIDU (nik, nama, id_adopter) VALUES (%s, %s, %s)")
            params.append((nik, nama, new_id))

        else:  # Organisasi
            npp  = request.POST.get("npp")
            nama_org = request.POST.get("nama_organisasi")
            if not npp or not nama_org:
                messages.error(request, "NPP dan nama organisasi wajib diisi.")
                return redirect('adopsi:register_adopter')

            sqls.append("INSERT INTO ORGANISASI (npp, nama_organisasi, id_adopter) VALUES (%s, %s, %s)")
            params.append((npp, nama_org, new_id))

        if execute_transaction(sqls, params):
            messages.success(request, "Adopter berhasil didaftarkan.")
            return redirect('adopsi:list_adopters')
        else:
            messages.error(request, "Gagal mendaftarkan adopter. Coba lagi.")

    candidates = execute_query(
        """
        SELECT p.username_p
        FROM PENGUNJUNG p
        LEFT JOIN ADOPTER a ON p.username_p = a.username_adopter
        WHERE a.username_adopter IS NULL
        """, ()
    )
    return render(request, 'adopter_form.html', {'candidates': candidates})

# List Status Adopsi Hewan (READ)
@require_http_methods(["GET"])
def list_adoptions(request):
    if not (is_admin(request) or is_pengunjung(request)):
        return redirect('main:login')

    if is_admin(request):
        rows = execute_query("""
            SELECT
                h.id               AS id_hewan,
                h.nama             AS nama_hewan,
                h.spesies,
                h.status_kesehatan AS kondisi,
                h.url_foto         AS url_foto,
                CASE
                WHEN o.status_pembayaran = 'tertunda' THEN 'Menunggu Pembayaran'
                WHEN o.status_pembayaran = 'lunas'
                    AND o.tgl_mulai_adopsi <= CURRENT_DATE
                    AND o.tgl_berhenti_adopsi >  CURRENT_DATE THEN 'Diadopsi'
                ELSE 'Tidak Diadopsi'
                END AS status,
                o.id_adopter,
                o.tgl_mulai_adopsi
            FROM HEWAN h
            LEFT JOIN ADOPSI o
                ON h.id = o.id_hewan
            AND (
                    o.status_pembayaran = 'tertunda'
                OR ( o.status_pembayaran = 'lunas'
                    AND o.tgl_mulai_adopsi <= CURRENT_DATE
                    AND o.tgl_berhenti_adopsi >  CURRENT_DATE
                   )
                )
            ORDER BY h.nama
        """, ())

    elif is_pengunjung(request):
        id_adopter = ensure_adopter(request)
        rows = execute_query(
            """
            SELECT
            h.id AS id_hewan,
            h.nama AS nama_hewan,
            h.spesies,
            h.status_kesehatan AS kondisi,
            h.url_foto AS url_foto,
            o.status_pembayaran AS raw_status,
            CASE
              WHEN o.status_pembayaran = 'tertunda' THEN 'Menunggu Pembayaran'
              WHEN o.status_pembayaran = 'lunas'     THEN 'Diadopsi'
            END AS status,
            o.id_adopter,
            o.tgl_mulai_adopsi
            FROM ADOPSI o
            JOIN HEWAN h ON o.id_hewan = h.id
            WHERE o.id_adopter = %s
              AND o.status_pembayaran IN ('tertunda','lunas')
              AND o.tgl_mulai_adopsi <= CURRENT_DATE
              AND o.tgl_berhenti_adopsi >  CURRENT_DATE
            ORDER BY o.tgl_mulai_adopsi DESC
            """,
            (id_adopter,)
        )

    paginator = Paginator(rows, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'adoption_list.html', {
        'page_obj': page_obj,
        'is_pengunjung': is_pengunjung(request),
        'is_admin': is_admin(request),
    })


# Buat Adopsi Hewan (CREATE)
@require_http_methods(["GET", "POST"])
def create_adoption(request, hewan_id):
    if not is_admin(request):
        return redirect('main:login')

    if request.method == "POST":
        id_adopter = request.POST.get("id_adopter")
        bulan      = int(request.POST.get("periode"))
        kontribusi = int(request.POST.get("kontribusi_finansial"))
        status     = 'tertunda'

        dup = execute_query(
            """
            SELECT 1
            FROM ADOPSI
            WHERE id_adopter = %s
              AND id_hewan   = %s
              AND tgl_mulai_adopsi = CURRENT_DATE
            """,
            (id_adopter, hewan_id)
        )
        if dup:
            messages.error(request,
                "Anda sudah membuat adopsi untuk hewan ini hari ini. "
                "Silakan coba lagi besok.")
            return redirect('adopsi:create_adoption', hewan_id=hewan_id)

        not_avail = execute_query(
            """
            SELECT 1
            FROM ADOPSI
            WHERE id_hewan = %s
              AND CURRENT_DATE >= tgl_mulai_adopsi
              AND CURRENT_DATE < tgl_berhenti_adopsi
            """,
            (hewan_id,)
        )
        if not_avail:
            messages.error(request, "Maaf, hewan ini sedang diadopsi pengguna lain.")
            return redirect('adopsi:create_adoption', hewan_id=hewan_id)

        if kontribusi <= 0:
            messages.error(request, "Nominal kontribusi harus lebih besar dari 0.")
            return redirect('adopsi:create_adoption', hewan_id=hewan_id)

        sqls = [
            """
            INSERT INTO ADOPSI
              (id_adopter, id_hewan, status_pembayaran,
               tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial)
            VALUES (
              %s, %s, %s,
              CURRENT_DATE,
              CURRENT_DATE + INTERVAL '%s months',
              %s
            )
            """,
        ]
        params = [
            (id_adopter, hewan_id, status, bulan, kontribusi),
            (kontribusi, id_adopter)
        ]

        if execute_transaction(sqls, params):
            messages.success(request, "Adopsi berhasil dibuat.")
            return redirect('adopsi:list_adoptions')
        else:
            messages.error(request, "Gagal membuat adopsi.")

    hewan = execute_query(
        "SELECT nama AS nama_hewan, spesies AS jenis_hewan FROM HEWAN WHERE id = %s",
        (hewan_id,)
    )
    if not hewan:
        return redirect('adopsi:list_adoptions')

    return render(request, 'adoption_form.html', {
      'hewan_id': hewan_id,
      'hewan': hewan[0],
    })

@require_http_methods(["GET", "POST"])
def adoption_detail(request, id_adopter, hewan_id, tgl_mulai):
    if not (is_admin(request) or is_pengunjung(request)):
        return redirect('main:login')

    rows = execute_query(
        """
        SELECT
          o.status_pembayaran,
          o.tgl_berhenti_adopsi,
          o.kontribusi_finansial AS nominal
        FROM ADOPSI o
        WHERE o.id_adopter=%s AND o.id_hewan=%s AND o.tgl_mulai_adopsi=%s
        """,
        (id_adopter, hewan_id, tgl_mulai)
    )
    if not rows:
        return redirect('adopsi:list_adoptions')
    detail = rows[0]
    old_end_date = detail['tgl_berhenti_adopsi']

    if request.method == "POST" and is_admin(request):
        if 'save_status' in request.POST:
            status_str = request.POST.get('status_pembayaran', detail['status_pembayaran'])
            contrib_str = request.POST.get('kontribusi_finansial', detail['nominal'])
            try:
                contrib = int(contrib_str)
            except (ValueError, TypeError):
                contrib = detail['nominal']

            end_date_str = request.POST.get('tgl_berhenti_adopsi', '').strip()
            if end_date_str:
                end_date = parse_date(end_date_str)
                if not end_date:
                    messages.error(request, "Format Tanggal Berhenti tidak valid.")
                    return redirect(request.path)
            else:
                end_date = old_end_date

            execute_query(
                """
                UPDATE ADOPSI
                SET status_pembayaran    = %s,
                    tgl_berhenti_adopsi  = %s,
                    kontribusi_finansial = %s
                WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s
                """,
                (status_str, end_date, contrib, id_adopter, hewan_id, tgl_mulai)
            )
            messages.success(request, "Status adopsi diperbarui.")

        elif 'stop_adoption' in request.POST:
            today = execute_query("SELECT CURRENT_DATE AS today", ())[0]['today']
            execute_query(
                """
                UPDATE ADOPSI
                SET tgl_berhenti_adopsi = %s
                WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s
                """,
                (today, id_adopter, hewan_id, tgl_mulai)
            )
            messages.success(request, "Adopsi dihentikan.")

        return redirect('adopsi:list_adoptions')

    detail_full = execute_query(
        """SELECT
             o.id_adopter, o.id_hewan, o.tgl_mulai_adopsi,
             o.tgl_berhenti_adopsi, o.status_pembayaran,
             o.kontribusi_finansial AS nominal,
             p.nama_depan||' '||p.nama_belakang AS nama_adopter,
             h.nama     AS nama_hewan,
             h.spesies  AS jenis_hewan,
             h.nama_habitat AS habitat,
             h.url_foto
           FROM ADOPSI o
           JOIN ADOPTER a  ON o.id_adopter = a.id_adopter
           JOIN PENGGUNA p  ON a.username_adopter = p.username
           JOIN HEWAN    h  ON o.id_hewan = h.id
           WHERE o.id_adopter=%s AND o.id_hewan=%s AND o.tgl_mulai_adopsi=%s
        """,
        (id_adopter, hewan_id, tgl_mulai)
    )[0]

    return render(request, 'adoption_detail.html', {
        'detail': detail_full,
        'is_admin': is_admin(request),
        'is_pengunjung': is_pengunjung(request),
    })


# Modal Sertifikat Adopsi
@require_http_methods(["GET"])
def adoption_certificate(request, hewan_id, tgl_mulai):
    if 'pengunjung' not in request.session.get('roles', []):
        return redirect('main:login')

    id_adopter = ensure_adopter(request)
    cert = execute_query(
        """
        SELECT
          CASE
            WHEN i.id_adopter IS NOT NULL THEN i.nama
            ELSE org.nama_organisasi
          END AS adopter_nama,
          h.spesies       AS jenis_hewan,
          h.nama          AS nama_hewan,
          o.tgl_mulai_adopsi,
          o.tgl_berhenti_adopsi
        FROM ADOPSI o
        JOIN HEWAN h ON o.id_hewan = h.id
        JOIN ADOPTER a ON o.id_adopter = a.id_adopter
        LEFT JOIN INDIVIDU i ON a.id_adopter = i.id_adopter
        LEFT JOIN ORGANISASI org ON a.id_adopter = org.id_adopter
        WHERE o.id_adopter=%s AND o.id_hewan=%s AND o.tgl_mulai_adopsi=%s
        """,
        (id_adopter, hewan_id, tgl_mulai)
    )[0]
    return render(request, 'user_adoption_certificate.html', {
        'cert': cert
    })

# Modal Laporan Kondisi Hewan
@require_http_methods(["GET"])
def adoption_report(request, hewan_id, tgl_mulai):
    if 'pengunjung' not in request.session.get('roles', []):
        return redirect('main:login')

    id_adopter = ensure_adopter(request)
    # cari adopsi untuk dapatkan tanggal mulai
    row = execute_query(
        "SELECT tgl_mulai_adopsi FROM ADOPSI "
        "WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s",
        (id_adopter, hewan_id, tgl_mulai)
    )
    tgl_mulai_adopsi = row[0]['tgl_mulai_adopsi']

    hewan = execute_query(
        """
        SELECT
          nama        AS nama_hewan,
          spesies     AS jenis_hewan,
          nama_habitat AS habitat
        FROM HEWAN
        WHERE id = %s
        """,
        (hewan_id,)
    )[0]

    medis = execute_query(
        """
        SELECT
          cm.tanggal_pemeriksaan,
          p.nama_depan||' '||p.nama_belakang AS nama_dokter,
          cm.status_kesehatan,
          cm.diagnosis,
          cm.pengobatan,
          cm.catatan_tindak_lanjut
        FROM CATATAN_MEDIS cm
        JOIN DOKTER_HEWAN dh ON cm.username_dh = dh.username_DH
        JOIN PENGGUNA p        ON dh.username_DH = p.username
        WHERE cm.id_hewan=%s
          AND cm.tanggal_pemeriksaan >= %s
        ORDER BY cm.tanggal_pemeriksaan DESC
        """,
        (hewan_id, tgl_mulai_adopsi)
    )
    return render(request, 'user_adoption_report.html', {
        'hewan': hewan,
        'medis': medis
    })

# Form Perpanjang Periode Adopsi (GET + POST)
@require_http_methods(["GET", "POST"])
def extend_adoption(request, hewan_id, tgl_mulai):
    if 'pengunjung' not in request.session.get('roles', []):
        return redirect('main:login')

    username = request.session['username']
    id_adopter = ensure_adopter(request)

    adp = execute_query(
        """
        SELECT
          o.status_pembayaran,
          o.tgl_berhenti_adopsi,
          i.nik,
          i.nama    AS individu_nama,
          org.npp,
          org.nama_organisasi
        FROM ADOPSI o
        LEFT JOIN INDIVIDU i    ON o.id_adopter = i.id_adopter
        LEFT JOIN ORGANISASI org ON o.id_adopter = org.id_adopter
        WHERE
          o.id_adopter     = %s
          AND o.id_hewan   = %s
          AND o.tgl_mulai_adopsi = %s
        """,
        (id_adopter, hewan_id, tgl_mulai)
    )
    if not adp:
        return redirect('adopsi:list_adoptions')
    adp = adp[0]

    peng = execute_query(
        "SELECT alamat FROM PENGUNJUNG WHERE username_p = %s",
        (username,)
    )[0]

    usr = execute_query(
        "SELECT nama_depan, nama_belakang, no_telepon FROM PENGGUNA WHERE username = %s",
        (username,)
    )[0]

    hw = execute_query(
        "SELECT nama AS nama_hewan, spesies FROM HEWAN WHERE id = %s",
        (hewan_id,)
    )[0]

    is_individual = bool(adp.get('nik'))

    if request.method == "POST":
        if adp['status_pembayaran'] != 'lunas':
            messages.error(request, "Hanya adopsi yang sudah lunas yang bisa diperpanjang.")
            return redirect('adopsi:extend_adoption', hewan_id=hewan_id, tgl_mulai=tgl_mulai)
        tambahan = int(request.POST['kontribusi_finansial'])
        bulan     = int(request.POST['periode'])

        sqls = [
            """
            UPDATE ADOPSI
            SET
                tgl_berhenti_adopsi  = tgl_berhenti_adopsi + INTERVAL '%s months',
                kontribusi_finansial = kontribusi_finansial + %s
            WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s
            """,
        ]
        params = [
            (bulan, tambahan, id_adopter, hewan_id, tgl_mulai),
            (tambahan, id_adopter)
        ]
        if tambahan <= 0:
            messages.error(request, "Nominal tambahan harus lebih besar dari 0.")
            return redirect('adopsi:extend_adoption', hewan_id=hewan_id, tgl_mulai=tgl_mulai)
        
        if execute_transaction(sqls, params):
            messages.success(request, "Periode adopsi berhasil diperpanjang.")
        else:
            messages.error(request, "Gagal memperpanjang adopsi.")
        return redirect('adopsi:list_adoptions')

    return render(request, 'user_extend_form.html', {
        'hewan_id':       hewan_id,
        'tgl_mulai':      tgl_mulai,
        'adp':            adp,
        'pengunjung':     peng,
        'pengguna':       usr,
        'hewan':          hw,
        'is_individual':  is_individual,
        'id_adopter':     id_adopter,
    })

# Modal Konfirmasi Hentikan Adopsi
@require_http_methods(["POST"])
def stop_adoption_user(request, hewan_id, tgl_mulai):
    if 'pengunjung' not in request.session.get('roles', []):
        return redirect('main:login')

    id_adopter = ensure_adopter(request)
    today = execute_query("SELECT CURRENT_DATE AS today", ())[0]['today']
    execute_query(
        """
        UPDATE ADOPSI
        SET tgl_berhenti_adopsi = %s
        WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s
        """,
        (today, id_adopter, hewan_id, tgl_mulai)
    )
    messages.success(request, "Adopsi telah dihentikan.")
    return redirect('adopsi:list_adoptions')

# Modal Riwayat Adopsi Adopter
@require_http_methods(["GET"])
def admin_adopter_history(request, id_adopter):
    if not is_admin(request):
        return redirect('main:login')

    # Data header adopter
    adopter = execute_query(
        """
        SELECT
          CASE
            WHEN i.id_adopter IS NOT NULL THEN i.nama
            ELSE org.nama_organisasi
          END AS nama_adopter,
          p_alamat.alamat,
          p_pengguna.no_telepon
        FROM ADOPTER a
        JOIN PENGUNJUNG p_alamat    ON a.username_adopter = p_alamat.username_p
        JOIN PENGGUNA p_pengguna   ON a.username_adopter = p_pengguna.username
        LEFT JOIN INDIVIDU i       ON a.id_adopter = i.id_adopter
        LEFT JOIN ORGANISASI org   ON a.id_adopter = org.id_adopter
        WHERE a.id_adopter = %s
        """,
        (id_adopter,)
    )[0]

    # Riwayat adopsi (status lunas, semua periode)
    today = execute_query("SELECT CURRENT_DATE AS today", ())[0]['today']
    history = execute_query(
        """
        SELECT
          o.id_hewan,
          h.nama        AS nama_hewan,
          h.spesies     AS jenis_hewan,
          o.tgl_mulai_adopsi,
          o.tgl_berhenti_adopsi,
          o.kontribusi_finansial
        FROM ADOPSI o
        JOIN HEWAN h ON o.id_hewan = h.id
        WHERE o.id_adopter = %s
          AND o.status_pembayaran = 'lunas'
        ORDER BY o.tgl_mulai_adopsi DESC
        """,
        (id_adopter,)
    )

    return render(request, 'admin_adopter_history.html', {
        'adopter': adopter,
        'history': history,
        'today': today,
        'id_adopter': id_adopter,
    })

# Admin Hapus Adopter (POST)
@require_http_methods(["POST"])
def admin_delete_adopter(request, id_adopter):
    if not is_admin(request):
        return redirect('main:login')

    # Cek aktif mengadopsi saat ini
    still_active = execute_query("""
        SELECT 1
        FROM ADOPSI
        WHERE id_adopter = %s
          AND tgl_mulai_adopsi <= CURRENT_DATE
          AND tgl_berhenti_adopsi >= CURRENT_DATE
    """, (id_adopter,))
    if still_active:
        messages.error(request, "Adopter masih aktif berpartisipasi dalam program adopsi dan tidak dapat dihapus.")
    else:
        execute_query("DELETE FROM ADOPTER WHERE id_adopter = %s", (id_adopter,))
        messages.success(request, "Adopter berhasil dihapus. Riwayat adopsi terhapus secara otomatis.") 

    return redirect('adopsi:list_adopters')


# Admin Hapus Data Adopsi (POST)
@require_http_methods(["POST"])
def admin_delete_adoption(request, id_adopter, hewan_id, tgl_mulai):
    if not is_admin(request):
        return redirect('main:login')

    row = execute_query(
        """
        SELECT kontribusi_finansial
        FROM ADOPSI
        WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s
        """,
        (id_adopter, hewan_id, tgl_mulai)
    )
    if not row:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:list_adopters')

    nominal = row[0]['kontribusi_finansial']

    sqls = [
        "DELETE FROM ADOPSI WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s",
    ]
    params = [
        (id_adopter, hewan_id, tgl_mulai),
        (nominal, id_adopter)
    ]
    execute_transaction(sqls, params)

    messages.success(request, "Data adopsi berhasil dihapus.")
    return redirect('adopsi:list_adopters')
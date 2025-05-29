from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from utils.db_connection import execute_query, execute_transaction
import uuid, datetime
# from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator
from django.http import JsonResponse

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

    adopters = execute_query(
        """
        SELECT
          a.username_adopter,
          a.id_adopter,
          a.total_kontribusi,
          CASE
            WHEN i.id_adopter IS NOT NULL THEN 'Individu'
            ELSE 'Organisasi'
          END AS tipe
        FROM ADOPTER a
        LEFT JOIN INDIVIDU i  ON a.id_adopter = i.id_adopter
        LEFT JOIN ORGANISASI o ON a.id_adopter = o.id_adopter
        """, ()
    )
    return render(request, 'adopter_list.html', {'adopters': adopters})

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

    # GET: pilih PENGUNJUNG yang belum jadi ADOPTER
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

    context = {
        'is_admin': is_admin(request),
        'is_pengunjung': is_pengunjung(request),
    }

    if is_admin(request):
        rows = execute_query(
            """
            SELECT
              h.id               AS id_hewan,
              h.nama             AS nama_hewan,
              h.spesies,
              h.status_kesehatan AS kondisi,
              h.url_foto         AS url_foto,
              CASE WHEN o.id_adopter IS NULL THEN 'Tidak Diadopsi' ELSE 'Diadopsi' END AS status,
              o.id_adopter,
              o.tgl_mulai_adopsi
            FROM HEWAN h
            LEFT JOIN ADOPSI o
              ON h.id = o.id_hewan
             AND o.tgl_mulai_adopsi <= CURRENT_DATE
             AND o.tgl_berhenti_adopsi >= CURRENT_DATE
            ORDER BY h.nama
            """, ()
        )
        paginator = Paginator(rows, 8)
        context['page_obj'] = paginator.get_page(request.GET.get('page'))

    elif is_pengunjung(request):
        id_adopter = ensure_adopter(request)
        print(id_adopter)
        rows = execute_query(
            """
            SELECT
              h.id               AS id_hewan,
              h.nama             AS nama_hewan,
              h.spesies,
              h.status_kesehatan AS kondisi,
              h.url_foto         AS url_foto,
              'Diadopsi'         AS status,
              o.id_adopter,
              o.tgl_mulai_adopsi
            FROM ADOPSI o
            JOIN HEWAN h ON o.id_hewan = h.id
            WHERE o.id_adopter = %s
            ORDER BY o.tgl_mulai_adopsi DESC
            """,
            (id_adopter,)
        )

    paginator = Paginator(rows, 8 )
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
        periode    = int(request.POST.get("periode"))
        start      = datetime.date.today()
        end        = start + relativedelta(months=periode) # type: ignore
        kontribusi = int(request.POST.get("kontribusi_finansial"))
        status     = 'tertunda'

        sqls = [
            """
            INSERT INTO ADOPSI
            (id_adopter, id_hewan, status_pembayaran,
             tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            "UPDATE ADOPTER SET total_kontribusi = total_kontribusi + %s WHERE id_adopter = %s"
        ]
        params = [
            (id_adopter, hewan_id, status, start, end, kontribusi),
            (kontribusi, id_adopter)
        ]

        if execute_transaction(sqls, params):
            messages.success(request, "Adopsi berhasil dibuat.")
            return redirect('adopsi:list_adoptions')
        messages.error(request, "Gagal membuat adopsi.")

    hewan = execute_query(
      "SELECT nama AS nama_hewan, spesies AS jenis_hewan FROM HEWAN WHERE id = %s",
      (hewan_id,)
    )
    if not hewan:
        messages.error(request, "Data hewan tidak ditemukan.")
        return redirect('adopsi:list_adoptions')

    return render(request, 'adoption_form.html', {
      'hewan_id': hewan_id,
      'hewan': hewan[0],
    })

@require_http_methods(["GET", "POST"])
def adoption_detail(request, id_adopter, hewan_id, tgl_mulai):
    if not (is_admin(request) or is_pengunjung(request)):
        return redirect('main:login')

    # ADMIN hanya yang boleh POST (update status / hentikan)
    if request.method == "POST" and is_admin(request):
        if 'save_status' in request.POST:
            status   = request.POST['status_pembayaran']
            end_date = request.POST['tgl_berhenti_adopsi']
            contrib  = int(request.POST['kontribusi_finansial'])
            execute_query(
                """
                UPDATE ADOPSI
                SET status_pembayaran    = %s,
                    tgl_berhenti_adopsi  = %s,
                    kontribusi_finansial = %s
                WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s
                """,
                (status, end_date, contrib, id_adopter, hewan_id, tgl_mulai)
            )
            messages.success(request, "Status adopsi diperbarui.")
        elif 'stop_adoption' in request.POST:
            today = datetime.date.today()
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

    # FETCH DETAIL (shared query)
    detail = execute_query(
        """
        SELECT
          o.id_adopter,
          o.id_hewan,
          o.tgl_mulai_adopsi,
          o.tgl_berhenti_adopsi,
          o.status_pembayaran,
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
    )
    if not detail:
        messages.error(request, "Detail adopsi tidak ditemukan.")
        return redirect('adopsi:home')
    detail = detail[0]

    return render(request, 'adoption_detail.html', {
        'detail': detail,
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
        messages.error(request, "Data adopsi tidak ditemukan.")
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
        tambahan = int(request.POST['kontribusi_finansial'])
        bulan     = int(request.POST['periode'])
        old_end   = adp['tgl_berhenti_adopsi']
        new_end   = old_end + relativedelta(months=bulan)

        sqls = [
            """
            UPDATE ADOPSI
            SET tgl_berhenti_adopsi  = %s,
                kontribusi_finansial = kontribusi_finansial + %s
            WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s
            """,
            "UPDATE ADOPTER SET total_kontribusi = total_kontribusi + %s WHERE id_adopter = %s"
        ]
        params = [
            (new_end, tambahan, id_adopter, hewan_id, tgl_mulai),
            (tambahan, id_adopter)
        ]
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
    today = datetime.date.today()
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

# Daftar Adopter + Top-5 Kontribusi Setahun
@require_http_methods(["GET"])
def admin_list_adopters(request):
    if not is_admin(request):
        return redirect('main:login')

    adopters = execute_query("SELECT username_adopter, total_kontribusi FROM ADOPTER", ())

    today = datetime.date.today()
    one_year_ago = today - relativedelta(years=1)

    # top 5 adopters by contributions in the last year
    top5 = execute_query(
        """
        SELECT
        a.username_adopter,
        SUM(o.kontribusi_finansial) AS total_contrib
        FROM ADOPSI o
        JOIN ADOPTER a ON o.id_adopter = a.id_adopter
        WHERE 
        (o.tgl_mulai_adopsi   BETWEEN %s AND %s)
        OR
        (o.tgl_berhenti_adopsi BETWEEN %s AND %s)
        GROUP BY a.username_adopter
        ORDER BY total_contrib DESC
        LIMIT 5
        """,
        (one_year_ago, today, one_year_ago, today)
    )

    return render(request, "adopter_list.html", {
        "adopters": adopters,
        "top_adopters": top5,
    })

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
    today = datetime.date.today()
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

    execute_query(
        "DELETE FROM ADOPTER WHERE id_adopter = %s",
        (id_adopter,)
    )
    messages.success(request, "Adopter berhasil dihapus.")
    return redirect('adopsi:admin_list_adopters')


# Admin Hapus Data Adopsi (POST)
@require_http_methods(["POST"])
def admin_delete_adoption(request, id_adopter, hewan_id, tgl_mulai):
    if not is_admin(request):
        return redirect('main:login')

    # Ambil nominal untuk dikurangi dari total_kontribusi
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
        return redirect('adopsi:admin_list_adopters')

    nominal = row[0]['kontribusi_finansial']

    sqls = [
        "DELETE FROM ADOPSI WHERE id_adopter=%s AND id_hewan=%s AND tgl_mulai_adopsi=%s",
        "UPDATE ADOPTER SET total_kontribusi = total_kontribusi - %s WHERE id_adopter = %s"
    ]
    params = [
        (id_adopter, hewan_id, tgl_mulai),
        (nominal, id_adopter)
    ]
    execute_transaction(sqls, params)

    messages.success(request, "Data adopsi berhasil dihapus.")
    return redirect('adopsi:admin_list_adopters')
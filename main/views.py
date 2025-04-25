from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from utils.db_connection import execute_query, execute_transaction

def home(request):
    return render(request, 'main.html')

@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        username      = request.POST.get("username")
        email         = request.POST.get("email")
        password      = request.POST.get("password")
        nama_depan    = request.POST.get("nama_depan")
        nama_tengah   = request.POST.get("nama_tengah") or None
        nama_belakang = request.POST.get("nama_belakang")
        no_telepon    = request.POST.get("no_telepon")
        alamat        = request.POST.get("alamat")
        tgl_lahir     = request.POST.get("tgl_lahir")  

        sqls = [
            """
            INSERT INTO PENGGUNA
            (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            """
            INSERT INTO PENGUNJUNG
            (username_p, alamat, tgl_lahir)
            VALUES (%s,%s,%s)
            """
        ]
        params = [
            (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon),
            (username, alamat, tgl_lahir)
        ]

        success = execute_transaction(sqls, params)
        if success:
            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect("login")
        else:
            messages.error(request, "Registrasi gagal: username mungkin sudah terdaftar.")

    return render(request, "register.html")


@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        rows = execute_query(
            "SELECT password FROM PENGGUNA WHERE username = %s",
            (username,)
        )
        print(rows)
        if rows and rows[0]["password"] == password:
            print("masuk")
            request.session["username"] = username
            messages.success(request, f"Selamat datang, {username}!")
            return redirect("main:home")
        else:
            print("masuk2")
            messages.error(request, "Username atau password salah.")

    return render(request, "login.html")


@require_http_methods(["POST"])
def logout(request):
    request.session.flush()
    messages.info(request, "Anda telah logout.")
    return redirect("login")

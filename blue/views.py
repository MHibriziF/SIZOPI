from django.shortcuts import render, redirect

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
    #     """
    #     """,
    # )

    return render(request, 'wahana.html')

def kelola_atraksi(request):
    if 'admin' not in request.session["roles"] :
        return redirect('main:dashboard')
    
    # data_atraksi = execute_query(
    #     """
    #     """,
    # )
    
    
    return render(request, 'atraksi.html')

def kelola_pengunjung(request):
    return render(request, 'kelola_pengunjung.html')


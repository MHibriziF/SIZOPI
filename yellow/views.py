from django.shortcuts import render

def hewan_list_view(request):
    return render(request, 'manage_satwa/hewan_list.html')

def habitat_list_view(request):
    return render(request, 'manage_habitat/habitat_list.html')
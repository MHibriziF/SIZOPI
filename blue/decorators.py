from django.shortcuts import redirect

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('username'):
            return redirect('main:login')
        if 'admin' not in request.session["roles"] :
            return redirect('main:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

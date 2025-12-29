from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')
def profile_view(request):
    user = request.user
    # Simple profile context; expand as needed
    context = {
        'user_obj': user,
    }
    return render(request, 'profile.html', context)

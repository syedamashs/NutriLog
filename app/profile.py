from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Profile

@login_required(login_url='/login/')
def profile_view(request):
    user = request.user
    # Ensure profile exists (signal should handle creation but be safe)
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Update basic user fields
        username = request.POST.get('username')
        email = request.POST.get('email')
        if username:
            user.username = username.strip()
        if email:
            user.email = email.strip()
        user.save()

        # Update profile numeric fields safely
        age = request.POST.get('age')
        height = request.POST.get('height_cm')
        weight = request.POST.get('weight_kg')
        try:
            profile.age = int(age) if age not in (None, '') else None
        except ValueError:
            profile.age = None
        try:
            profile.height_cm = float(height) if height not in (None, '') else None
        except ValueError:
            profile.height_cm = None
        try:
            profile.weight_kg = float(weight) if weight not in (None, '') else None
        except ValueError:
            profile.weight_kg = None

        # Sex: accept M/F/O or clear if invalid
        sex = request.POST.get('sex')
        if sex in ('M', 'F', 'O'):
            profile.sex = sex
        else:
            profile.sex = None

        profile.save()
        messages.success(request, 'Profile updated successfully')
        return redirect(reverse('profile'))

    context = {
        'user_obj': user,
        'profile': profile,
        'bmi': profile.bmi(),
        'bmi_category': profile.bmi_category,
        'bmr': profile.bmr(),
        'ideal_weight': profile.ideal_weight_kg(),
    }
    return render(request, 'profile.html', context)

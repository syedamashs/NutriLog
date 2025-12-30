from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

#Login_View
def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"]
        )
        if user:
            login(request, user)
            return redirect("/")
        return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")

#Register_View
def register_view(request):
    if request.method == "POST":
        username = request.POST.get('username','').strip()
        email = request.POST.get('email','').strip()
        password = request.POST.get('password','')
        password2 = request.POST.get('password2','')

        # optional personal fields
        age = request.POST.get('age','').strip()
        height_cm = request.POST.get('height_cm','').strip()
        weight_kg = request.POST.get('weight_kg','').strip()
        sex = request.POST.get('sex','').strip()

        errors = []
        if not username:
            errors.append('Username is required')
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        if password != password2:
            errors.append('Passwords do not match')
        if User.objects.filter(username=username).exists():
            errors.append('Username is already taken')
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists')

        if errors:
            return render(request, 'register.html', {'errors': errors, 'username': username, 'email': email, 'age': age, 'height_cm': height_cm, 'weight_kg': weight_kg, 'sex': sex})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        # Ensure Profile exists and save additional attributes
        try:
            from .models import Profile
            profile, _ = Profile.objects.get_or_create(user=user)
            try:
                profile.age = int(age) if age not in (None, '') else None
            except ValueError:
                profile.age = None
            try:
                profile.height_cm = float(height_cm) if height_cm not in (None, '') else None
            except ValueError:
                profile.height_cm = None
            try:
                profile.weight_kg = float(weight_kg) if weight_kg not in (None, '') else None
            except ValueError:
                profile.weight_kg = None
            if sex in ('M', 'F', 'O'):
                profile.sex = sex
            profile.save()
        except Exception:
            # Non-fatal; registration still succeeds
            pass

        return redirect('/login/')
    return render(request, "register.html")

#LogOut_View
def logout_view(request):
    logout(request)
    return redirect("/login/")

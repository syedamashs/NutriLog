from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

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


def register_view(request):
    if request.method == "POST":
        username = request.POST.get('username','').strip()
        email = request.POST.get('email','').strip()
        password = request.POST.get('password','')
        password2 = request.POST.get('password2','')

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
            return render(request, 'register.html', {'errors': errors, 'username': username, 'email': email})

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return redirect('/login/')
    return render(request, "register.html")


def logout_view(request):
    logout(request)
    return redirect("/login/")

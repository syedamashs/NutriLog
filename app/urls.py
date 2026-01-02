from django.contrib import admin
from django.urls import path, include
from django.urls import path
from .views import home, how_it_works, pricing, dashboard, history, analytics, analytics_logs
from .views_auth import login_view, register_view, logout_view
from .profile import profile_view

urlpatterns = [
    path('', home, name='home'),
    path('how-it-works/', how_it_works, name='how_it_works'),
    path('pricing/', pricing, name='pricing'),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('history/', history, name='history'),  
    path('analytics/', analytics, name='analytics'),
    path('analytics/logs/', analytics_logs, name='analytics_logs'),
    path('logout/', logout_view),
    path('profile/', profile_view, name='profile'),
    path('admin/', admin.site.urls), 
]

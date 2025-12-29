from django.contrib import admin
from django.urls import path, include
from django.urls import path
from .views import dashboard, history, analytics, analytics_logs
from .views_auth import login_view, register_view, logout_view
from .profile import profile_view

urlpatterns = [
    path('', dashboard),
    path('login/', login_view),
    path('register/', register_view),
    path('history/', history, name='history'),  
    path('analytics/', analytics, name='analytics'),
    path('analytics/logs/', analytics_logs, name='analytics_logs'),
    path('logout/', logout_view),
    path('profile/', profile_view),
    path('admin/', admin.site.urls), 
]

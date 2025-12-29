from django.urls import path
from .views import dashboard
from .views_auth import login_view, register_view, logout_view
from .profile import profile_view

urlpatterns = [
    path('', dashboard),
    path('login/', login_view),
    path('register/', register_view),
    path('logout/', logout_view),
    path('profile/', profile_view),
]

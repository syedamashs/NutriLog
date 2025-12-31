from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('', include('app.urls')),
]

# In development, serve /media/ and /data/ from the filesystem for convenience
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.DATA_URL, document_root=settings.DATA_ROOT)

# Developer convenience: allow serving /data/ locally even when DEBUG=False (controlled by setting)
# NOTE: Only enable SERVE_DATA_LOCALLY for local testing; in production serve data via your web server/CDN.
if getattr(settings, 'SERVE_DATA_LOCALLY', False):
    urlpatterns += [path('data/<path:path>', serve, {'document_root': settings.DATA_ROOT})]

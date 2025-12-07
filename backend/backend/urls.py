from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('interfaz.urls')),  # Incluir las URLs de interfaz
]
# Solo en desarrollo: servir archivos multimedia
# Esta condición DEBE estar FUERA de las urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # No necesitas agregar static() aquí porque Django ya lo maneja
from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),  # CAMBIO: login_view en vez de index
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    
    # Páginas principales
    path('home/', views.seleccionar_generos, name='home'),
    path('guardar-generos/', views.guardar_generos, name='guardar_generos'),
    path('lista-reproduccion/', views.lista_reproduccion, name='lista_reproduccion'),
]


from django.urls import path
from . import views

urlpatterns = [
    path('', views.seleccionar_generos, name='home'),  # Página principal
    path('guardar-generos/', views.guardar_generos, name='guardar_generos'),
]
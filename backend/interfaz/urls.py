from django.urls import path
from . import views

urlpatterns = [
    path('', views.seleccionar_generos, name='home'),
    path('guardar-generos/', views.guardar_generos, name='guardar_generos'),
    path('lista-reproduccion/', views.lista_reproduccion, name='lista_reproduccion'),
]
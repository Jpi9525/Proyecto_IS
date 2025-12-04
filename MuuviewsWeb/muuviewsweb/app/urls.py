from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='LoginScreen'),

    path('login/', views.login, name='login'),
    path('registro/',views.registro, name='registro'),
    path('guardar-usuario/', views.guardar_usuario, name='guardar_usuario'),
    path('main/', views.main, name='main'),
    path('logout/', views.logout, name='logout'),

]
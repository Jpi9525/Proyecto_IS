from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('guardar-usuario/', views.guardar_usuario, name='guardar_usuario'),
    path('logout/', views.logout_view, name='logout'),
    
    # Páginas principales
    path('home/', views.seleccionar_generos, name='home'),
    path('guardar-generos/', views.guardar_generos, name='guardar_generos'),
    path('lista-reproduccion/', views.lista_reproduccion, name='lista_reproduccion'),
    
    # === AGREGAR ESTAS RUTAS ===
    # Álbumes
    path('albumes/', views.lista_albumes, name='lista_albumes'),
    path('album/<int:album_id>/', views.ver_album, name='ver_album'),
    
    # Playlists
    path('playlists/', views.mis_playlists, name='mis_playlists'),
    path('playlist/<int:playlist_id>/', views.ver_playlist, name='ver_playlist'),
    
    # Favoritos
    path('favoritos/', views.mis_favoritos, name='mis_favoritos'),
    # === AGREGAR ESTAS RUTAS ===
    # Favoritos AJAX
    path('api/favorito/toggle/', views.toggle_favorito, name='toggle_favorito'),
    
    # Playlists AJAX
    path('api/playlist/crear/', views.crear_playlist, name='crear_playlist'),
    path('api/playlist/agregar-cancion/', views.agregar_cancion_playlist, name='agregar_cancion_playlist'),
    path('api/playlist/quitar-cancion/', views.quitar_cancion_playlist, name='quitar_cancion_playlist'),
    path('api/playlists/usuario/', views.obtener_playlists_usuario, name='obtener_playlists_usuario'),
]
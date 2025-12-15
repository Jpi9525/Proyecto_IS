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
        # Descargas Offline
    path('musica-offline/', views.musica_offline, name='musica_offline'),
    path('api/descargar/cancion/', views.descargar_cancion, name='descargar_cancion'),
    path('api/descargar/album/', views.descargar_album, name='descargar_album'),
    path('api/descargar/playlist/', views.descargar_playlist, name='descargar_playlist'),
    path('api/verificar-descarga/', views.verificar_descarga, name='verificar_descarga'),
    path('api/playlist/actualizar-portada/', views.actualizar_portada_playlist, name='actualizar_portada_playlist'),
    path('api/playlist/toggle-visibilidad/', views.toggle_visibilidad_playlist, name='toggle_visibilidad_playlist'),
    path('api/playlist/renombrar/', views.renombrar_playlist, name='renombrar_playlist'),
    path('api/playlist/eliminar/', views.eliminar_playlist, name='eliminar_playlist'),
    # Perfil de usuario
    path('lista-reproduccion/perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('lista-reproduccion/perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('lista-reproduccion/perfil/red-social/<int:red_id>/eliminar/', views.eliminar_red_social, name='eliminar_red_social'),
    
    # Compartir canción
    path('cancion/<int:cancion_id>/compartir/', views.compartir_cancion, name='compartir_cancion'),
    # Reseñas
    path('api/resenas/cancion/<int:cancion_id>/', views.obtener_resenas_cancion, name='obtener_resenas_cancion'),
    path('api/resena/agregar/', views.agregar_resena, name='agregar_resena'),
    path('api/resena/eliminar/', views.eliminar_resena, name='eliminar_resena'),
    path('api/resena/like/', views.reaccionar_resena, name='reaccionar_resena'),

    # Artistas y Admin
    path('api/solicitar-artista/', views.solicitar_artista, name='solicitar_artista'),
    path('subir-album/', views.subir_album, name='subir_album'),
    path('admin/solicitudes/', views.panel_admin_artistas, name='panel_admin_artistas'),
]
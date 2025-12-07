from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('guardar-usuario/', views.guardar_usuario, name='guardar_usuario'),  # IMPORTANTE
    path('logout/', views.logout_view, name='logout'),
    
    # Páginas principales
    path('home/', views.seleccionar_generos, name='home'),  # Esta es la de géneros
    path('guardar-generos/', views.guardar_generos, name='guardar_generos'),
    path('lista-reproduccion/', views.lista_reproduccion, name='lista_reproduccion'),
    
    # Perfil
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    # Géneros
    path('generos/', views.seleccionar_generos, name='seleccionar_generos'),

    # Redes Sociales
    path('perfil/eliminar-red/<int:red_id>/', views.eliminar_red_social, name='eliminar_red_social'),

    # Álbumes
    path('albumes/', views.lista_albumes, name='lista_albumes'),
    path('album/<int:album_id>/', views.ver_album, name='ver_album'),

    # Playlists
    path('playlists/', views.mis_playlists, name='mis_playlists'),
    path('playlist/<int:playlist_id>/', views.ver_playlist, name='ver_playlist'),

    # Favoritos
    path('favoritos/', views.mis_favoritos, name='mis_favoritos'),

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
   
    #Buscar Canciones
    path('buscar-canciones/', views.buscar_canciones, name='buscar_canciones'),

    #Reacciones en cancion y valoraciones
    path('reaccionar-cancion/', views.reaccionar_cancion, name='reaccionar_cancion'),
    path('calificar-cancion/', views.calificar_cancion, name='calificar_cancion'),
    path('rating-estadisticas/<int:cancion_id>/', views.obtener_estadisticas_rating, name='estadisticas_rating'),

]

# Esto permite que Django sirva las fotos subidas (solo en modo DEBUG)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

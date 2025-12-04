from django.db import models

class Generos(models.Model):
    genero_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=25)
    imagen_path = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'generos'

    def __str__(self):
        return self.nombre


class Albumes(models.Model):
    album_id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=50, blank=True, null=True)
    imagen_portada_path = models.CharField(max_length=500, blank=True, null=True)
    fecha_lanzamiento = models.DateField(blank=True, null=True)
    permitir_descarga = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'albumes'

    def __str__(self):
        return self.titulo


class Artistas(models.Model):
    artista_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, blank=True, null=True)
    biografia = models.CharField(max_length=500, blank=True, null=True)
    sitio_web_url = models.CharField(max_length=100, blank=True, null=True)
    usuario_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'artistas'

    def __str__(self):
        return self.nombre


class Canciones(models.Model):
    cancion_id = models.AutoField(primary_key=True)
    album = models.ForeignKey(Albumes, models.DO_NOTHING, blank=True, null=True, db_column='album_id')
    titulo = models.CharField(max_length=15, blank=True, null=True)
    duracion = models.TimeField(blank=True, null=True)
    ruta_archivo = models.CharField(max_length=200, blank=True, null=True)
    tamano_archivo = models.BigIntegerField(blank=True, null=True)
    num_reproducciones = models.IntegerField(blank=True, null=True)
    permitir_descarga = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'canciones'

    def __str__(self):
        return self.titulo if self.titulo else f"Canción {self.cancion_id}"


class CancionesGeneros(models.Model):
    cancion = models.ForeignKey(Canciones, models.DO_NOTHING, blank=True, null=True, db_column='cancion_id')
    genero = models.ForeignKey(Generos, models.DO_NOTHING, blank=True, null=True, db_column='genero_id')

    class Meta:
        managed = False
        db_table = 'canciones_generos'


class CancionesArtistas(models.Model):
    tipo_participacion = models.CharField(max_length=11, blank=True, null=True)
    cancion = models.ForeignKey(Canciones, models.DO_NOTHING, blank=True, null=True, db_column='cancion_id')
    artista = models.ForeignKey(Artistas, models.DO_NOTHING, blank=True, null=True, db_column='artista_id')

    class Meta:
        managed = False
        db_table = 'canciones_artistas'

class Usuario(models.Model):
    usuario_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)  # Aumentado
    apellido = models.CharField(max_length=100, blank=True, null=True)  # Aumentado
    contrasena = models.CharField(max_length=255, blank=True, null=True)  # Aumentado
    email = models.CharField(max_length=100, blank=True, null=True)  # AUMENTADO de 30 a 100
    foto_perfil_path = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    es_email_verificado = models.IntegerField(blank=True, null=True, default=0)
    es_admin = models.IntegerField(blank=True, null=True, default=0)
    cancion_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuarios'

class Playlist(models.Model):
    playlist_id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='usuario_id', blank=True, null=True)
    nombre = models.CharField(max_length=30, blank=True, null=True)
    fecha_creacion = models.DateField(blank=True, null=True)
    imagen_portada = models.CharField(max_length=500, blank=True, null=True)
    es_publica = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'playlists'


class PlaylistsCanciones(models.Model):
    playlist = models.ForeignKey(Playlist, models.DO_NOTHING, db_column='playlist_id')
    cancion = models.ForeignKey(Canciones, models.DO_NOTHING, db_column='cancion_id')
    orden = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'playlists_canciones'


class FavoritosCanciones(models.Model):
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='usuario_id')
    cancion = models.ForeignKey(Canciones, models.DO_NOTHING, db_column='cancion_id')
    es_favorito = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'favoritos_canciones'


class FavoritosAlbumes(models.Model):
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='usuario_id')
    album = models.ForeignKey(Albumes, models.DO_NOTHING, db_column='album_id')
    es_favorito = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'favoritos_albumes'
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
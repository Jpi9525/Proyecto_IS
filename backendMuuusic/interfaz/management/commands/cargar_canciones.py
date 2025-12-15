from django.core.management.base import BaseCommand
from django.db import connection
import requests

class Command(BaseCommand):
    help = 'Cargar canciones desde Jamendo API'

    def handle(self, *args, **options):
        API_KEY = 'b3785e8e'  # Tu API Key
        
        generos_map = {
            'rock': 'Rock',
            'pop': 'Pop', 
            'jazz': 'Jazz',
            'electronic': 'Electronic',
            'hiphop': 'Hip-hop',
            'classical': 'Classical',
            'reggae': 'Reggae',
            'metal': 'Metal',
        }
        
        with connection.cursor() as cursor:
            for tag, genero_nombre in generos_map.items():
                self.stdout.write(f'Buscando canciones de {genero_nombre}...')
                
                url = f"https://api.jamendo.com/v3.0/tracks/?client_id={API_KEY}&format=json&limit=10&tags={tag}&audioformat=mp32"
                
                try:
                    response = requests.get(url)
                    data = response.json()
                    
                    if data.get('results'):
                        for track in data['results']:
                            # Obtener o crear género
                            cursor.execute("SELECT genero_id FROM generos WHERE nombre = %s", [genero_nombre])
                            genero_row = cursor.fetchone()
                            
                            if not genero_row:
                                cursor.execute("INSERT INTO generos (nombre) VALUES (%s)", [genero_nombre])
                                cursor.execute("SELECT LAST_INSERT_ID()")
                                genero_id = cursor.fetchone()[0]
                            else:
                                genero_id = genero_row[0]
                            
                            # Crear artista
                            artista_nombre = track['artist_name'][:30]
                            cursor.execute("SELECT artista_id FROM artistas WHERE nombre = %s", [artista_nombre])
                            artista_row = cursor.fetchone()
                            
                            if not artista_row:
                                cursor.execute("INSERT INTO artistas (nombre) VALUES (%s)", [artista_nombre])
                                cursor.execute("SELECT LAST_INSERT_ID()")
                                artista_id = cursor.fetchone()[0]
                            else:
                                artista_id = artista_row[0]
                            
                            # Crear álbum
                            album_titulo = (track.get('album_name', 'Single') or 'Single')[:50]
                            album_imagen = track.get('album_image', track.get('image', ''))
                            
                            cursor.execute("SELECT album_id FROM albumes WHERE titulo = %s", [album_titulo])
                            album_row = cursor.fetchone()
                            
                            if not album_row:
                                cursor.execute("""
                                    INSERT INTO albumes (titulo, imagen_portada_path) 
                                    VALUES (%s, %s)
                                """, [album_titulo, album_imagen])
                                cursor.execute("SELECT LAST_INSERT_ID()")
                                album_id = cursor.fetchone()[0]
                            else:
                                album_id = album_row[0]
                            
                            # Crear canción
                            titulo = track['name'][:15]
                            duracion_segundos = int(track['duration'])
                            mins = duracion_segundos // 60
                            secs = duracion_segundos % 60
                            duracion = f"00:{mins:02d}:{secs:02d}"
                            ruta_audio = track['audio']
                            
                            # Verificar si la canción ya existe
                            cursor.execute("SELECT cancion_id FROM canciones WHERE titulo = %s AND album_id = %s", [titulo, album_id])
                            if cursor.fetchone():
                                self.stdout.write(f'  - {titulo} ya existe, saltando...')
                                continue
                            
                            cursor.execute("""
                                INSERT INTO canciones (album_id, titulo, duracion, ruta_archivo, num_reproducciones)
                                VALUES (%s, %s, %s, %s, 0)
                            """, [album_id, titulo, duracion, ruta_audio])
                            cursor.execute("SELECT LAST_INSERT_ID()")
                            cancion_id = cursor.fetchone()[0]
                            
                            # Relacionar canción con género
                            cursor.execute("""
                                INSERT INTO canciones_generos (cancion_id, genero_id)
                                VALUES (%s, %s)
                            """, [cancion_id, genero_id])
                            
                            # Relacionar canción con artista
                            cursor.execute("""
                                INSERT INTO canciones_artistas (cancion_id, artista_id, tipo_participacion)
                                VALUES (%s, %s, 'Principal')
                            """, [cancion_id, artista_id])
                            
                            self.stdout.write(f'  ✓ {titulo} - {artista_nombre}')
                            
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error en {genero_nombre}: {e}'))
        
        self.stdout.write(self.style.SUCCESS('¡Canciones cargadas exitosamente!'))
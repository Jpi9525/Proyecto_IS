import os
import sys
import django
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

# API Key de Jamendo (gratis)
JAMENDO_CLIENT_ID = "2c9a11b9"  # Client ID público de prueba

def cargar_generos():
    """Cargar géneros musicales básicos"""
    generos = [
        'Rock', 'Pop', 'Jazz', 'Hip-hop', 'Electronic', 
        'Classical', 'Reggae', 'Metal', 'Country', 'R&B'
    ]
    
    with connection.cursor() as cursor:
        for genero in generos:
            cursor.execute("""
                INSERT IGNORE INTO generos (nombre) VALUES (%s)
            """, [genero])
    
    print(f"✅ {len(generos)} géneros cargados")


def obtener_canciones_jamendo(genero, limite=15):
    """Obtener canciones de Jamendo por género"""
    url = "https://api.jamendo.com/v3.0/tracks/"
    
    # Mapeo de géneros a tags de Jamendo
    tags_map = {
        'Rock': 'rock',
        'Pop': 'pop',
        'Jazz': 'jazz',
        'Hip-hop': 'hiphop',
        'Electronic': 'electronic',
        'Classical': 'classical',
        'Reggae': 'reggae',
        'Metal': 'metal',
        'Country': 'country',
        'R&B': 'rnb'
    }
    
    tag = tags_map.get(genero, genero.lower())
    
    params = {
        'client_id': JAMENDO_CLIENT_ID,
        'format': 'json',
        'limit': limite,
        'tags': tag,
        'include': 'musicinfo',
        'audioformat': 'mp32',
        'order': 'popularity_total'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data.get('results'):
            print(f"  📥 Encontradas {len(data['results'])} canciones de {genero}")
            return data['results']
        else:
            print(f"  ⚠️ No se encontraron canciones para {genero}")
            return []
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def guardar_cancion_en_bd(cancion, genero_nombre):
    """Guardar una canción en la base de datos"""
    try:
        with connection.cursor() as cursor:
            # 1. Crear o obtener artista
            artista_nombre = cancion.get('artist_name', 'Artista Desconocido')[:30]
            
            cursor.execute("SELECT artista_id FROM artistas WHERE nombre = %s", [artista_nombre])
            result = cursor.fetchone()
            
            if result:
                artista_id = result[0]
            else:
                cursor.execute("INSERT INTO artistas (nombre) VALUES (%s)", [artista_nombre])
                cursor.execute("SELECT LAST_INSERT_ID()")
                artista_id = cursor.fetchone()[0]
            
            # 2. Crear álbum
            album_nombre = cancion.get('album_name', 'Single')[:50]
            album_imagen = cancion.get('album_image') or cancion.get('image', '')
            
            cursor.execute("SELECT album_id FROM albumes WHERE titulo = %s", [album_nombre])
            result = cursor.fetchone()
            
            if result:
                album_id = result[0]
            else:
                cursor.execute("""
                    INSERT INTO albumes (titulo, imagen_portada_path, permitir_descarga)
                    VALUES (%s, %s, 1)
                """, [album_nombre, album_imagen])
                cursor.execute("SELECT LAST_INSERT_ID()")
                album_id = cursor.fetchone()[0]
                
                # Relacionar álbum con artista
                cursor.execute("""
                    INSERT IGNORE INTO albumes_artistas (album_id, artista_id, rol)
                    VALUES (%s, %s, 'Principal')
                """, [album_id, artista_id])
            
            # 3. Crear canción
            titulo = cancion.get('name', 'Sin título')[:15]
            duracion_seg = int(cancion.get('duration', 0))
            minutos = duracion_seg // 60
            segundos = duracion_seg % 60
            duracion = f"00:{minutos:02d}:{segundos:02d}"
            ruta_audio = cancion.get('audio', '')
            
            # Verificar si ya existe
            cursor.execute("SELECT cancion_id FROM canciones WHERE ruta_archivo = %s", [ruta_audio])
            if cursor.fetchone():
                return None  # Ya existe
            
            cursor.execute("""
                INSERT INTO canciones (album_id, titulo, duracion, ruta_archivo, permitir_descarga, num_reproducciones)
                VALUES (%s, %s, %s, %s, 1, 0)
            """, [album_id, titulo, duracion, ruta_audio])
            cursor.execute("SELECT LAST_INSERT_ID()")
            cancion_id = cursor.fetchone()[0]
            
            # 4. Relacionar canción con artista
            cursor.execute("""
                INSERT IGNORE INTO canciones_artistas (cancion_id, artista_id, tipo_participacion)
                VALUES (%s, %s, 'Principal')
            """, [cancion_id, artista_id])
            
            # 5. Relacionar canción con género
            cursor.execute("SELECT genero_id FROM generos WHERE nombre = %s", [genero_nombre])
            genero_result = cursor.fetchone()
            
            if genero_result:
                cursor.execute("""
                    INSERT IGNORE INTO canciones_generos (cancion_id, genero_id)
                    VALUES (%s, %s)
                """, [cancion_id, genero_result[0]])
            
            print(f"    ✅ '{titulo}' - {artista_nombre}")
            return cancion_id
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None


def cargar_todas_las_canciones():
    """Cargar canciones de todos los géneros"""
    generos = ['Rock', 'Pop', 'Jazz', 'Hip-hop', 'Electronic', 
               'Classical', 'Reggae', 'Metal', 'Country', 'R&B']
    
    total = 0
    
    for genero in generos:
        print(f"\n🎵 {genero}...")
        canciones = obtener_canciones_jamendo(genero, limite=15)
        
        for cancion in canciones:
            if guardar_cancion_en_bd(cancion, genero):
                total += 1
    
    return total


def verificar_bd():
    """Mostrar estadísticas de la BD"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM canciones")
        total_canciones = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM artistas")
        total_artistas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM albumes")
        total_albumes = cursor.fetchone()[0]
        
        print(f"\n📊 Base de datos:")
        print(f"   🎵 Canciones: {total_canciones}")
        print(f"   🎤 Artistas: {total_artistas}")
        print(f"   💿 Álbumes: {total_albumes}")
        
        cursor.execute("""
            SELECT g.nombre, COUNT(cg.cancion_id) as total
            FROM generos g 
            LEFT JOIN canciones_generos cg ON g.genero_id = cg.genero_id 
            GROUP BY g.genero_id, g.nombre
            ORDER BY total DESC
        """)
        
        print(f"\n📊 Canciones por género:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}")


if __name__ == "__main__":
    print("=" * 50)
    print("🎵 CARGADOR DE CANCIONES - JAMENDO")
    print("=" * 50)
    
    print("\n1️⃣ Cargando géneros...")
    cargar_generos()
    
    print("\n2️⃣ Descargando canciones de Jamendo...")
    total = cargar_todas_las_canciones()
    
    print(f"\n✅ Se cargaron {total} canciones nuevas")
    
    verificar_bd()
    
    print("\n🎉 ¡Listo! Ahora corre: python manage.py runserver")
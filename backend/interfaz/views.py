
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import connection
import json
import random

def seleccionar_generos(request):
    """Vista principal para mostrar el formulario de selección de géneros"""
    
    # Rutas correctas según tu estructura
    imagenes_generos = {
        'Rock': 'interfaz/imagenes/generos/gen_vaca_rockera.png',
        'Pop': 'interfaz/imagenes/generos/gen_vaca_pop.png',
        'Jazz': 'interfaz/imagenes/generos/gen_vaca_jazz.png',
        'Hip-hop': 'interfaz/imagenes/generos/gen_vaca_hiphop.png',
        'Electronic': 'interfaz/imagenes/generos/gen_vaca_electronica.png',
        'Classical': 'interfaz/imagenes/generos/gen_vaca_clasica.png',
        'Reggae': 'interfaz/imagenes/generos/gen_vaca_reggaeton.png',
        'Metal': 'interfaz/imagenes/generos/gen_vaca_metal.png',
        'Country': 'interfaz/imagenes/generos/gen_vaca_alternativo.png',
        'R&B': 'interfaz/imagenes/generos/gen_vaca_rb.png',
    }
    
    try:
        from .models import Generos
        generos_db = Generos.objects.all()
        
        if generos_db.exists():
            generos = []
            for g in generos_db[:10]:
                imagen_path = imagenes_generos.get(g.nombre, 'interfaz/imagenes/generos/gen_vaca_alternativo.png')
                generos.append({
                    'nombre': g.nombre,
                    'valor': g.nombre,
                    'imagen': imagen_path,
                    'usar_static': True
                })
        else:
            generos = []
            for nombre, imagen_path in imagenes_generos.items():
                generos.append({
                    'nombre': nombre,
                    'valor': nombre,
                    'imagen': imagen_path,
                    'usar_static': True
                })
    except Exception as e:
        print(f"Error: {e}")
        generos = []
        for nombre, imagen_path in imagenes_generos.items():
            generos.append({
                'nombre': nombre,
                'valor': nombre,
                'imagen': imagen_path,
                'usar_static': True
            })
    
    # DEBUG: Imprimir para verificar
    print(f"Géneros a mostrar: {len(generos)}")
    for g in generos:
        print(f"  - {g['nombre']}: {g['imagen']}")
    
    context = {
        'generos': generos
    }
    return render(request, 'interfaz/seleccionar_generos.html', context)


def guardar_generos(request):
    """Vista para procesar los géneros seleccionados"""
    if request.method == 'POST':
        # Verificar si es petición AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                generos_seleccionados = data.get('generos', [])
            except:
                generos_seleccionados = request.POST.getlist('generos')
        else:
            generos_seleccionados = request.POST.getlist('generos')
        
        # Validaciones
        if len(generos_seleccionados) != 3:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Debes seleccionar exactamente 3 géneros'})
            messages.error(request, 'Debes seleccionar exactamente 3 géneros')
            return redirect('home')
        
        # Guardar en sesión
        request.session['generos_favoritos'] = generos_seleccionados
        
        # Debug
        print(f"✅ Géneros seleccionados: {generos_seleccionados}")
        
        # Respuesta AJAX o redirección normal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Géneros guardados exitosamente',
                'generos': generos_seleccionados,
                'redirect_url': '/lista-reproduccion/'
            })
        
        return redirect('lista_reproduccion')
    
    return redirect('home')


def lista_reproduccion(request):
    """Vista para mostrar las canciones reales de la BD"""
    generos_seleccionados = request.session.get('generos_favoritos', [])
    
    if not generos_seleccionados or len(generos_seleccionados) != 3:
        messages.warning(request, 'Primero debes seleccionar 3 géneros musicales')
        return redirect('home')
    
    todas_las_canciones = []
    
    try:
        # Usar SQL directo para obtener las canciones
        with connection.cursor() as cursor:
            # Query para obtener canciones con sus relaciones
            query = """
                SELECT 
                    c.cancion_id,
                    c.titulo,
                    c.duracion,
                    c.ruta_archivo,
                    a.titulo as album,
                    a.imagen_portada_path,
                    ar.nombre as artista,
                    g.nombre as genero
                FROM canciones c
                LEFT JOIN albumes a ON c.album_id = a.album_id
                LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id 
                    AND ca.tipo_participacion = 'Principal'
                LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                LEFT JOIN canciones_generos cg ON c.cancion_id = cg.cancion_id
                LEFT JOIN generos g ON cg.genero_id = g.genero_id
                WHERE g.nombre IN (%s, %s, %s)
                ORDER BY RAND()
                LIMIT 10
            """
            
            cursor.execute(query, generos_seleccionados)
            canciones_db = cursor.fetchall()
            
            # Convertir resultados a diccionarios
            for cancion in canciones_db:
                # Formatear duración
                duracion = str(cancion[2]) if cancion[2] else "0:00"
                if len(duracion) > 5:  # Si viene como HH:MM:SS
                    duracion = duracion[3:8]  # Tomar solo MM:SS
                
                todas_las_canciones.append({
                    'id': cancion[0],
                    'titulo': cancion[1],
                    'duracion': duracion,
                    'ruta_archivo': cancion[3],
                    'album': cancion[4] if cancion[4] else 'Sin álbum',
                    'portada': cancion[5] if cancion[5] else 'https://via.placeholder.com/150?text=Sin+Portada',
                    'artista': cancion[6] if cancion[6] else 'Artista desconocido',
                    'genero': cancion[7]
                })
    except Exception as e:
        print(f"Error al obtener canciones de la BD: {e}")
        # Si hay error, usar canciones de ejemplo
        pass
    
    # Si no hay suficientes canciones en la BD, agregar de ejemplo
    if len(todas_las_canciones) < 10:
        canciones_faltantes = 10 - len(todas_las_canciones)
        for i in range(canciones_faltantes):
            todas_las_canciones.append({
                'id': f"demo_{i}",
                'titulo': f"Canción demo {i+1}",
                'duracion': "3:30",
                'ruta_archivo': '','album': "Álbum demo",
                'portada': 'https://via.placeholder.com/150?text=Demo',
                'artista': "Artista demo",
                'genero': random.choice(generos_seleccionados) if generos_seleccionados else 'Demo'
            })
    
    # Mezclar las canciones
    random.shuffle(todas_las_canciones)
    
    context = {
        'canciones': todas_las_canciones,
        'generos_seleccionados': generos_seleccionados,
        'total_canciones': len(todas_las_canciones)
    }
    
    return render(request, 'interfaz/lista_reproduccion.html', context)
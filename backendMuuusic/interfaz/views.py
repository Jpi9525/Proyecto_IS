
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.db import connection
from .models import Usuario, Generos
import json
import random

@csrf_exempt
def guardar_usuario(request):
    """Vista para guardar usuario después de verificación de email"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extraer datos
            nombre = data.get('name')
            email = data.get('email')
            username = data.get('username')
            password = data.get('password')
            
            # Verificar si el email ya existe
            if Usuario.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una cuenta con ese email'
                })
            
            # OPCIÓN 1: Crear usuario solo con campos que existen
            try:
                nuevo_usuario = Usuario(
                    nombre=username,
                    email=email,
                    contrasena=make_password(password)  # Hashear la contraseña
                )
                nuevo_usuario.save()
                
                # Actualizar campos adicionales con SQL directo si es necesario
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE usuarios 
                        SET es_email_verificado = 1, es_admin = 0, apellido = ''
                        WHERE usuario_id = %s
                    """, [nuevo_usuario.usuario_id])
                
            except Exception as e:
                # OPCIÓN 2: Si falla, usar SQL directo completamente
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO usuarios (nombre, apellido, email, contrasena, es_email_verificado, es_admin)
                        VALUES (%s, %s, %s, %s, 1, 0)
                    """, [username, '', email, password])
                    
                    # Obtener el ID del usuario recién creado
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    usuario_id = cursor.fetchone()[0]
                    
                    nuevo_usuario = Usuario.objects.get(usuario_id=usuario_id)
            
            # Auto-login después del registro
            request.session['usuario_id'] = nuevo_usuario.usuario_id
            request.session['usuario_nombre'] = nuevo_usuario.nombre
            request.session['usuario_email'] = nuevo_usuario.email
            
            return JsonResponse({
                'success': True,
                'message': 'Usuario registrado exitosamente',
                'redirect_url': '/home/'
            })
            
        except Exception as e:
            print(f"Error al guardar usuario: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


def login_view(request):
    """Vista para el login de usuarios"""
    if request.method == 'POST':
        username_or_email = request.POST.get('userName') or request.POST.get('email')
        password = request.POST.get('passWord') or request.POST.get('password')
        
        print(f"Datos recibidos - Usuario: {username_or_email}, Password: {password}")
        
        if not username_or_email or not password:
            messages.error(request, 'Por favor ingresa usuario/email y contraseña')
            return render(request, 'interfaz/LoginScreen.html')
        
        try:
            # Buscar usuario
            if '@' in str(username_or_email):
                usuario = Usuario.objects.get(email=username_or_email)
            else:
                usuario = Usuario.objects.get(nombre=username_or_email)
            
            print(f"Usuario encontrado: {usuario.nombre}")
            print(f"Contraseña en BD: '{usuario.contrasena}'")
            
            # ========== CAMBIO IMPORTANTE ==========
            # Verificar si la contraseña está hasheada o es texto plano
            password_valida = False
            
            if usuario.contrasena.startswith('pbkdf2_sha256$'):
                # Contraseña hasheada - usar check_password
                password_valida = check_password(password, usuario.contrasena)
            else:
                # Contraseña en texto plano (legacy)
                password_valida = (usuario.contrasena == password)
            
            if password_valida:
                # Login exitoso
                request.session['usuario_id'] = usuario.usuario_id
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_email'] = usuario.email
                
                print("✅ Login exitoso!")
                return redirect('lista_reproduccion')
            else:
                print("❌ Contraseña incorrecta")
                messages.error(request, 'Contraseña incorrecta')
                
        except Usuario.DoesNotExist:
            messages.error(request, 'No existe una cuenta con esos datos')
        except Usuario.MultipleObjectsReturned:
            messages.error(request, 'Error: Múltiples usuarios encontrados')
        except Exception as e:
            print(f"Error inesperado: {e}")
            messages.error(request, f'Error: {str(e)}')
        
        return render(request, 'interfaz/LoginScreen.html')
    
    return render(request, 'interfaz/LoginScreen.html')

def registro_view(request):
    """Vista para registro de nuevos usuarios"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validaciones
        if not all([nombre, apellido, email, password]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'interfaz/registro.html')
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'interfaz/registro.html')
        
        # Verificar si el email ya existe
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe una cuenta con ese email')
            return render(request, 'interfaz/registro.html')
        
        try:
            # Crear nuevo usuario
            nuevo_usuario = Usuario(
                nombre=nombre,
                apellido=apellido,
                email=email,
                contrasena=password,  # En producción usar make_password(password)
                foto_perfil_path='/static/interfaz/imagenes/inicio/default-avatar.png'
            )
            nuevo_usuario.save()
            
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error al crear la cuenta: {str(e)}')
            return render(request, 'interfaz/registro.html')
    
    return render(request, 'interfaz/registro.html')

def logout_view(request):
    """Vista para cerrar sesión"""
    request.session.flush()  # Limpiar toda la sesión
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login')

def seleccionar_generos(request):
    """Modificar la vista existente para requerir login"""
    # Verificar si el usuario está logueado
    if 'usuario_id' not in request.session:
        messages.warning(request, 'Debes iniciar sesión primero')
        return redirect('login')
    
    
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
    
    # Obtener datos del usuario
    usuario = None
    usuario_id = request.session.get('usuario_id')
    
    if usuario_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT usuario_id, nombre, foto_perfil_path
                    FROM usuarios
                    WHERE usuario_id = %s
                """, [usuario_id])
                row = cursor.fetchone()
                if row:
                    usuario = {
                        'id': row[0],
                        'nombre': row[1] or '',
                        'foto_perfil_path': row[2] or ''
                    }
        except Exception as e:
            print(f"Error obteniendo usuario: {e}")
    
    todas_las_canciones = []
    
    try:
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
            
            # Obtener IDs de canciones para consultas adicionales
            cancion_ids = [c[0] for c in canciones_db]
            
            # Obtener favoritos del usuario
            favoritos_usuario = set()
            if usuario_id and cancion_ids:
                placeholders = ','.join(['%s'] * len(cancion_ids))
                cursor.execute(f"""
                    SELECT cancion_id FROM favoritos_canciones 
                    WHERE usuario_id = %s AND cancion_id IN ({placeholders}) AND es_favorito = 1
                """, [usuario_id] + cancion_ids)
                favoritos_usuario = {row[0] for row in cursor.fetchall()}
            
            # Obtener ratings del usuario
            ratings_usuario = {}
            if usuario_id and cancion_ids:
                placeholders = ','.join(['%s'] * len(cancion_ids))
                cursor.execute(f"""
                    SELECT cancion_id, puntuacion_estrellas FROM resenas_canciones 
                    WHERE usuario_id = %s AND cancion_id IN ({placeholders})
                """, [usuario_id] + cancion_ids)
                ratings_usuario = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Obtener descargas del usuario
            descargas_usuario = set()
            if usuario_id and cancion_ids:
                placeholders = ','.join(['%s'] * len(cancion_ids))
                cursor.execute(f"""
                    SELECT cancion_id FROM descargas_offline 
                    WHERE usuario_id = %s AND cancion_id IN ({placeholders}) AND tipo = 'cancion'
                """, [usuario_id] + cancion_ids)
                descargas_usuario = {row[0] for row in cursor.fetchall()}
            
            # Convertir resultados a diccionarios
            for cancion in canciones_db:
                cancion_id = cancion[0]
                
                # Formatear duración
                duracion = str(cancion[2]) if cancion[2] else "0:00"
                if len(duracion) > 5:
                    duracion = duracion[3:8]
                
                todas_las_canciones.append({
                    'id': cancion_id,
                    'titulo': cancion[1],
                    'duracion': duracion,
                    'ruta_archivo': cancion[3],
                    'album': cancion[4] if cancion[4] else 'Sin álbum',
                    'portada': cancion[5] if cancion[5] else 'https://via.placeholder.com/150?text=Sin+Portada',
                    'artista': cancion[6] if cancion[6] else 'Artista desconocido',
                    'genero': cancion[7],
                    'es_favorito': cancion_id in favoritos_usuario,
                    'user_rating': ratings_usuario.get(cancion_id, 0),
                    'es_descargado': cancion_id in descargas_usuario
                })
                
    except Exception as e:
        print(f"Error al obtener canciones de la BD: {e}")
        import traceback
        traceback.print_exc()
    
    # Mezclar las canciones
    random.shuffle(todas_las_canciones)
    
    context = {
        'canciones': todas_las_canciones,
        'generos_seleccionados': generos_seleccionados,
        'total_canciones': len(todas_las_canciones),
        'usuario': usuario
    }
    
    return render(request, 'interfaz/lista_reproduccion.html', context)
# ============== ÁLBUMES ==============

def lista_albumes(request):
    """Ver todos los álbumes"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    albumes = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.album_id,
                    a.titulo,
                    a.imagen_portada_path,
                    a.fecha_lanzamiento,
                    ar.nombre as artista,
                    COUNT(c.cancion_id) as total_canciones
                FROM albumes a
                LEFT JOIN albumes_artistas aa ON a.album_id = aa.album_id AND aa.rol = 'Principal'
                LEFT JOIN artistas ar ON aa.artista_id = ar.artista_id
                LEFT JOIN canciones c ON a.album_id = c.album_id
                GROUP BY a.album_id, a.titulo, a.imagen_portada_path, a.fecha_lanzamiento, ar.nombre
                ORDER BY a.fecha_lanzamiento DESC
            """)
            
            for row in cursor.fetchall():
                albumes.append({
                    'id': row[0],
                    'titulo': row[1] or 'Sin título',
                    'portada': row[2] or 'https://via.placeholder.com/150?text=Album',
                    'fecha': row[3],
                    'artista': row[4] or 'Artista desconocido',
                    'total_canciones': row[5]
                })
    except Exception as e:
        print(f"Error: {e}")
    
    return render(request, 'interfaz/lista_album.html', {'albumes': albumes})


def ver_album(request, album_id):
    """Ver contenido de un álbum específico"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    album_info = None
    canciones = []
    
    try:
        with connection.cursor() as cursor:
            # Info del álbum
            cursor.execute("""
                SELECT 
                    a.album_id, a.titulo, a.imagen_portada_path, 
                    a.fecha_lanzamiento, ar.nombre as artista
                FROM albumes a
                LEFT JOIN albumes_artistas aa ON a.album_id = aa.album_id AND aa.rol = 'Principal'
                LEFT JOIN artistas ar ON aa.artista_id = ar.artista_id
                WHERE a.album_id = %s
            """, [album_id])
            
            row = cursor.fetchone()
            if row:
                album_info = {
                    'id': row[0],
                    'titulo': row[1] or 'Sin título',
                    'portada': row[2] or 'https://via.placeholder.com/300?text=Album',
                    'fecha': row[3],
                    'artista': row[4] or 'Artista desconocido'
                }
            
            # Canciones del álbum
            cursor.execute("""
                SELECT 
                    c.cancion_id, c.titulo, c.duracion, c.ruta_archivo,
                    ar.nombre as artista, g.nombre as genero
                FROM canciones c
                LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id AND ca.tipo_participacion = 'Principal'
                LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                LEFT JOIN canciones_generos cg ON c.cancion_id = cg.cancion_id
                LEFT JOIN generos g ON cg.genero_id = g.genero_id
                WHERE c.album_id = %s
                ORDER BY c.cancion_id
            """, [album_id])
            
            for row in cursor.fetchall():
                duracion = str(row[2]) if row[2] else "0:00"
                if len(duracion) > 5:
                    duracion = duracion[3:8]
                
                canciones.append({
                    'id': row[0],
                    'titulo': row[1] or 'Sin título',
                    'duracion': duracion,
                    'ruta_archivo': row[3],
                    'artista': row[4] or album_info['artista'],
                    'genero': row[5] or 'Sin género',
                    'portada': album_info['portada']
                })
    except Exception as e:
        print(f"Error: {e}")
    
    if not album_info:
        messages.error(request, 'Álbum no encontrado')
        return redirect('lista_albumes')
    
    return render(request, 'interfaz/ver_album.html', {
        'album': album_info,
        'canciones': canciones,
        'total_canciones': len(canciones)
    })


# ============== PLAYLISTS ==============

def mis_playlists(request):
    """Ver playlists del usuario"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    playlists = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.playlist_id, p.nombre, p.imagen_portada,
                    p.fecha_creacion, p.es_publica,
                    COUNT(pc.cancion_id) as total_canciones
                FROM playlists p
                LEFT JOIN playlists_canciones pc ON p.playlist_id = pc.playlist_id
                WHERE p.usuario_id = %s
                GROUP BY p.playlist_id, p.nombre, p.imagen_portada, p.fecha_creacion, p.es_publica
                ORDER BY p.fecha_creacion DESC
            """, [usuario_id])
            
            for row in cursor.fetchall():
                playlists.append({
                    'id': row[0],
                    'nombre': row[1] or 'Sin nombre',
                    'portada': row[2] or 'https://via.placeholder.com/150?text=Playlist',
                    'fecha': row[3],
                    'es_publica': row[4],
                    'total_canciones': row[5]
                })
    except Exception as e:
        print(f"Error: {e}")
    
    return render(request, 'interfaz/mis_playlist.html', {'playlists': playlists})


def ver_playlist(request, playlist_id):
    """Ver contenido de una playlist"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    playlist_info = None
    canciones = []
    
    try:
        with connection.cursor() as cursor:
            # Info de la playlist
            cursor.execute("""
                SELECT playlist_id, nombre, imagen_portada, fecha_creacion, es_publica, usuario_id
                FROM playlists
                WHERE playlist_id = %s AND (usuario_id = %s OR es_publica = 1)
            """, [playlist_id, usuario_id])
            
            row = cursor.fetchone()
            if row:
                playlist_info = {
                    'id': row[0],
                    'nombre': row[1] or 'Sin nombre',
                    'portada': row[2] or 'https://via.placeholder.com/300?text=Playlist',
                    'fecha': row[3],
                    'es_publica': row[4],
                    'es_propietario': row[5] == usuario_id
                }
            
            # Canciones de la playlist
            cursor.execute("""
                SELECT 
                    c.cancion_id, c.titulo, c.duracion, c.ruta_archivo,
                    a.titulo as album, a.imagen_portada_path,
                    ar.nombre as artista, g.nombre as genero, pc.orden
                FROM playlists_canciones pc
                JOIN canciones c ON pc.cancion_id = c.cancion_id
                LEFT JOIN albumes a ON c.album_id = a.album_id
                LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id AND ca.tipo_participacion = 'Principal'
                LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                LEFT JOIN canciones_generos cg ON c.cancion_id = cg.cancion_id
                LEFT JOIN generos g ON cg.genero_id = g.genero_id
                WHERE pc.playlist_id = %s
                ORDER BY pc.orden
            """, [playlist_id])
            
            for row in cursor.fetchall():
                duracion = str(row[2]) if row[2] else "0:00"
                if len(duracion) > 5:
                    duracion = duracion[3:8]
                
                canciones.append({
                    'id': row[0],
                    'titulo': row[1] or 'Sin título',
                    'duracion': duracion,
                    'ruta_archivo': row[3],
                    'album': row[4] or 'Sin álbum',
                    'portada': row[5] or 'https://via.placeholder.com/80?text=Song',
                    'artista': row[6] or 'Artista desconocido',
                    'genero': row[7] or 'Sin género'
                })
    except Exception as e:
        print(f"Error: {e}")
    
    if not playlist_info:
        messages.error(request, 'Playlist no encontrada')
        return redirect('mis_playlists')
    
    return render(request, 'interfaz/ver_playlist.html', {
        'playlist': playlist_info,
        'canciones': canciones,
        'total_canciones': len(canciones)
    })


# ============== FAVORITOS ==============

def mis_favoritos(request):
    """Ver canciones favoritas del usuario"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    canciones = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.cancion_id, c.titulo, c.duracion, c.ruta_archivo,
                    a.titulo as album, a.imagen_portada_path,
                    ar.nombre as artista, g.nombre as genero
                FROM favoritos_canciones fc
                JOIN canciones c ON fc.cancion_id = c.cancion_id
                LEFT JOIN albumes a ON c.album_id = a.album_id
                LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id AND ca.tipo_participacion = 'Principal'
                LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                LEFT JOIN canciones_generos cg ON c.cancion_id = cg.cancion_id
                LEFT JOIN generos g ON cg.genero_id = g.genero_id
                WHERE fc.usuario_id = %s AND fc.es_favorito = 1
            """, [usuario_id])
            
            for row in cursor.fetchall():
                duracion = str(row[2]) if row[2] else "0:00"
                if len(duracion) > 5:
                    duracion = duracion[3:8]
                
                canciones.append({
                    'id': row[0],
                    'titulo': row[1] or 'Sin título',
                    'duracion': duracion,
                    'ruta_archivo': row[3],
                    'album': row[4] or 'Sin álbum',
                    'portada': row[5] or 'https://via.placeholder.com/80?text=Song',
                    'artista': row[6] or 'Artista desconocido',
                    'genero': row[7] or 'Sin género'
                })
    except Exception as e:
        print(f"Error: {e}")
    
    return render(request, 'interfaz/mis_favoritos.html', {
        'canciones': canciones,
        'total_canciones': len(canciones)
    })

# ============== FAVORITOS AJAX ==============

@csrf_exempt
def toggle_favorito(request):
    """Agregar o quitar canción de favoritos"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        cancion_id = data.get('cancion_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar si ya existe en favoritos
            cursor.execute("""
                SELECT es_favorito FROM favoritos_canciones 
                WHERE usuario_id = %s AND cancion_id = %s
            """, [usuario_id, cancion_id])
            
            resultado = cursor.fetchone()
            
            if resultado:
                # Ya existe, toggle el estado
                nuevo_estado = 0 if resultado[0] == 1 else 1
                cursor.execute("""
                    UPDATE favoritos_canciones 
                    SET es_favorito = %s 
                    WHERE usuario_id = %s AND cancion_id = %s
                """, [nuevo_estado, usuario_id, cancion_id])
                es_favorito = nuevo_estado == 1
            else:
                # No existe, crear como favorito
                cursor.execute("""
                    INSERT INTO favoritos_canciones (usuario_id, cancion_id, es_favorito)
                    VALUES (%s, %s, 1)
                """, [usuario_id, cancion_id])
                es_favorito = True
        
        return JsonResponse({
            'success': True,
            'es_favorito': es_favorito,
            'message': 'Agregado a favoritos' if es_favorito else 'Quitado de favoritos'
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


# ============== PLAYLISTS AJAX ==============

@csrf_exempt
def obtener_playlists_usuario(request):
    """Obtener playlists del usuario para el modal"""
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    usuario_id = request.session['usuario_id']
    playlists = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT playlist_id, nombre, imagen_portada
                FROM playlists
                WHERE usuario_id = %s
                ORDER BY fecha_creacion DESC
            """, [usuario_id])
            
            for row in cursor.fetchall():
                playlists.append({
                    'id': row[0],
                    'nombre': row[1] or 'Sin nombre',
                    'portada': row[2] or ''
                })
        
        return JsonResponse({'success': True, 'playlists': playlists})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def crear_playlist(request):
    """Crear nueva playlist"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre', 'Mi Playlist')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO playlists (usuario_id, nombre, fecha_creacion, es_publica)
                VALUES (%s, %s, CURDATE(), 0)
            """, [usuario_id, nombre])
            
            # Obtener el ID de la playlist creada
            cursor.execute("SELECT LAST_INSERT_ID()")
            playlist_id = cursor.fetchone()[0]
        
        return JsonResponse({
            'success': True,
            'playlist_id': playlist_id,
            'nombre': nombre,
            'message': f'Playlist "{nombre}" creada'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def agregar_cancion_playlist(request):
    """Agregar canción a una playlist"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        cancion_id = data.get('cancion_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar que la playlist pertenece al usuario
            cursor.execute("""
                SELECT nombre FROM playlists 
                WHERE playlist_id = %s AND usuario_id = %s
            """, [playlist_id, usuario_id])
            
            playlist = cursor.fetchone()
            if not playlist:
                return JsonResponse({'success': False, 'message': 'Playlist no encontrada'})
            
            # Verificar si la canción ya está en la playlist
            cursor.execute("""
                SELECT 1 FROM playlists_canciones 
                WHERE playlist_id = %s AND cancion_id = %s
            """, [playlist_id, cancion_id])
            
            if cursor.fetchone():
                return JsonResponse({'success': False, 'message': 'La canción ya está en la playlist'})
            
            # Obtener el orden máximo actual
            cursor.execute("""
                SELECT COALESCE(MAX(orden), 0) + 1 FROM playlists_canciones 
                WHERE playlist_id = %s
            """, [playlist_id])
            nuevo_orden = cursor.fetchone()[0]
            
            # Agregar la canción
            cursor.execute("""
                INSERT INTO playlists_canciones (playlist_id, cancion_id, orden)
                VALUES (%s, %s, %s)
            """, [playlist_id, cancion_id, nuevo_orden])
        
        return JsonResponse({
            'success': True,
            'message': f'Canción agregada a "{playlist[0]}"'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def quitar_cancion_playlist(request):
    """Quitar canción de una playlist"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        cancion_id = data.get('cancion_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar que la playlist pertenece al usuario
            cursor.execute("""
                SELECT 1 FROM playlists 
                WHERE playlist_id = %s AND usuario_id = %s
            """, [playlist_id, usuario_id])
            
            if not cursor.fetchone():
                return JsonResponse({'success': False, 'message': 'Playlist no encontrada'})
            
            # Quitar la canción
            cursor.execute("""
                DELETE FROM playlists_canciones 
                WHERE playlist_id = %s AND cancion_id = %s
            """, [playlist_id, cancion_id])
        
        return JsonResponse({
            'success': True,
            'message': 'Canción eliminada de la playlist'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
    
# ============== DESCARGAS OFFLINE ==============

@csrf_exempt
def descargar_cancion(request):
    """Descargar una canción para offline"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        cancion_id = data.get('cancion_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar si ya está descargada
            cursor.execute("""
                SELECT 1 FROM descargas_offline 
                WHERE usuario_id = %s AND cancion_id = %s AND tipo = 'cancion'
            """, [usuario_id, cancion_id])
            
            if cursor.fetchone():
                # Ya existe, eliminar (toggle)
                cursor.execute("""
                    DELETE FROM descargas_offline 
                    WHERE usuario_id = %s AND cancion_id = %s AND tipo = 'cancion'
                """, [usuario_id, cancion_id])
                
                return JsonResponse({
                    'success': True,
                    'descargado': False,
                    'message': 'Canción eliminada de descargas'
                })
            else:
                # No existe, agregar
                cursor.execute("""
                    INSERT INTO descargas_offline (usuario_id, cancion_id, tipo)
                    VALUES (%s, %s, 'cancion')
                """, [usuario_id, cancion_id])
                
                return JsonResponse({
                    'success': True,
                    'descargado': True,
                    'message': 'Canción guardada para offline'
                })
                
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def descargar_album(request):
    """Descargar un álbum completo para offline"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        album_id = data.get('album_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar si ya está descargado
            cursor.execute("""
                SELECT 1 FROM descargas_offline 
                WHERE usuario_id = %s AND album_id = %s AND tipo = 'album'
            """, [usuario_id, album_id])
            
            if cursor.fetchone():
                # Eliminar álbum y sus canciones
                cursor.execute("""
                    DELETE FROM descargas_offline 
                    WHERE usuario_id = %s AND album_id = %s AND tipo = 'album'
                """, [usuario_id, album_id])
                
                # También eliminar las canciones del álbum
                cursor.execute("""
                    DELETE FROM descargas_offline 
                    WHERE usuario_id = %s AND tipo = 'cancion' AND cancion_id IN (
                        SELECT cancion_id FROM canciones WHERE album_id = %s
                    )
                """, [usuario_id, album_id])
                
                return JsonResponse({
                    'success': True,
                    'descargado': False,
                    'message': 'Álbum eliminado de descargas'
                })
            else:
                # Agregar álbum
                cursor.execute("""
                    INSERT INTO descargas_offline (usuario_id, album_id, tipo)
                    VALUES (%s, %s, 'album')
                """, [usuario_id, album_id])
                
                # Agregar todas las canciones del álbum
                cursor.execute("""
                    INSERT IGNORE INTO descargas_offline (usuario_id, cancion_id, tipo)
                    SELECT %s, cancion_id, 'cancion' FROM canciones WHERE album_id = %s
                """, [usuario_id, album_id])
                
                # Contar canciones agregadas
                cursor.execute("""
                    SELECT COUNT(*) FROM canciones WHERE album_id = %s
                """, [album_id])
                total_canciones = cursor.fetchone()[0]
                
                return JsonResponse({
                    'success': True,
                    'descargado': True,
                    'total_canciones': total_canciones,
                    'message': f'Álbum guardado ({total_canciones} canciones)'
                })
                
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def descargar_playlist(request):
    """Descargar una playlist completa para offline"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar si ya está descargada
            cursor.execute("""
                SELECT 1 FROM descargas_offline 
                WHERE usuario_id = %s AND playlist_id = %s AND tipo = 'playlist'
            """, [usuario_id, playlist_id])
            
            if cursor.fetchone():
                # Eliminar playlist
                cursor.execute("""
                    DELETE FROM descargas_offline 
                    WHERE usuario_id = %s AND playlist_id = %s AND tipo = 'playlist'
                """, [usuario_id, playlist_id])
                
                return JsonResponse({
                    'success': True,
                    'descargado': False,
                    'message': 'Playlist eliminada de descargas'
                })
            else:
                # Agregar playlist
                cursor.execute("""
                    INSERT INTO descargas_offline (usuario_id, playlist_id, tipo)
                    VALUES (%s, %s, 'playlist')
                """, [usuario_id, playlist_id])
                
                # Agregar canciones de la playlist
                cursor.execute("""
                    INSERT IGNORE INTO descargas_offline (usuario_id, cancion_id, tipo)
                    SELECT %s, cancion_id, 'cancion' FROM playlists_canciones WHERE playlist_id = %s
                """, [usuario_id, playlist_id])
                
                # Contar canciones
                cursor.execute("""
                    SELECT COUNT(*) FROM playlists_canciones WHERE playlist_id = %s
                """, [playlist_id])
                total_canciones = cursor.fetchone()[0]
                
                return JsonResponse({
                    'success': True,
                    'descargado': True,
                    'total_canciones': total_canciones,
                    'message': f'Playlist guardada ({total_canciones} canciones)'
                })
                
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


def musica_offline(request):
    """Vista para ver música descargada/offline del usuario"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    canciones = []
    albumes = []
    playlists = []
    
    try:
        with connection.cursor() as cursor:
            # Obtener canciones descargadas
            cursor.execute("""
                SELECT 
                    c.cancion_id, c.titulo, c.duracion, c.ruta_archivo,
                    a.titulo as album, a.imagen_portada_path,
                    ar.nombre as artista, g.nombre as genero,
                    d.fecha_descarga
                FROM descargas_offline d
                JOIN canciones c ON d.cancion_id = c.cancion_id
                LEFT JOIN albumes a ON c.album_id = a.album_id
                LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id 
                    AND ca.tipo_participacion = 'Principal'
                LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                LEFT JOIN canciones_generos cg ON c.cancion_id = cg.cancion_id
                LEFT JOIN generos g ON cg.genero_id = g.genero_id
                WHERE d.usuario_id = %s AND d.tipo = 'cancion'
                ORDER BY d.fecha_descarga DESC
            """, [usuario_id])
            
            for row in cursor.fetchall():
                duracion = str(row[2]) if row[2] else "0:00"
                if len(duracion) > 5:
                    duracion = duracion[3:8]
                
                canciones.append({
                    'id': row[0],
                    'titulo': row[1] or 'Sin título',
                    'duracion': duracion,
                    'ruta_archivo': row[3],
                    'album': row[4] or 'Sin álbum',
                    'portada': row[5] or 'https://via.placeholder.com/80?text=Song',
                    'artista': row[6] or 'Artista desconocido',
                    'genero': row[7] or 'Sin género',
                    'fecha_descarga': row[8]
                })
            
            # Obtener álbumes descargados
            cursor.execute("""
                SELECT 
                    a.album_id, a.titulo, a.imagen_portada_path,
                    ar.nombre as artista,
                    COUNT(c.cancion_id) as total_canciones,
                    d.fecha_descarga
                FROM descargas_offline d
                JOIN albumes a ON d.album_id = a.album_id
                LEFT JOIN albumes_artistas aa ON a.album_id = aa.album_id AND aa.rol = 'Principal'
                LEFT JOIN artistas ar ON aa.artista_id = ar.artista_id
                LEFT JOIN canciones c ON a.album_id = c.album_id
                WHERE d.usuario_id = %s AND d.tipo = 'album'
                GROUP BY a.album_id, a.titulo, a.imagen_portada_path, ar.nombre, d.fecha_descarga
                ORDER BY d.fecha_descarga DESC
            """, [usuario_id])
            
            for row in cursor.fetchall():
                albumes.append({
                    'id': row[0],
                    'titulo': row[1] or 'Sin título',
                    'portada': row[2] or 'https://via.placeholder.com/150?text=Album',
                    'artista': row[3] or 'Artista desconocido',
                    'total_canciones': row[4],
                    'fecha_descarga': row[5]
                })
            
            # Obtener playlists descargadas
            cursor.execute("""
                SELECT 
                    p.playlist_id, p.nombre, p.imagen_portada,
                    COUNT(pc.cancion_id) as total_canciones,
                    d.fecha_descarga
                FROM descargas_offline d
                JOIN playlists p ON d.playlist_id = p.playlist_id
                LEFT JOIN playlists_canciones pc ON p.playlist_id = pc.playlist_id
                WHERE d.usuario_id = %s AND d.tipo = 'playlist'
                GROUP BY p.playlist_id, p.nombre, p.imagen_portada, d.fecha_descarga
                ORDER BY d.fecha_descarga DESC
            """, [usuario_id])
            
            for row in cursor.fetchall():
               playlists.append({
                    'id': row[0],
                    'nombre': row[1] or 'Sin nombre',
                    'portada': row[2] or 'https://via.placeholder.com/150?text=Playlist',
                    'total_canciones': row[3],
                    'fecha_descarga': row[4]
                })
                
    except Exception as e:
        print(f"Error: {e}")
    
    context = {
        'canciones': canciones,
        'albumes': albumes,
        'playlists': playlists,
        'total_canciones': len(canciones),
        'total_albumes': len(albumes),
        'total_playlists': len(playlists)
    }
    
    return render(request, 'interfaz/musica_offline.html', context)


@csrf_exempt
def verificar_descarga(request):
    """Verificar si un item está descargado"""
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False})
    
    tipo = request.GET.get('tipo')  # 'cancion', 'album', 'playlist'
    item_id = request.GET.get('id')
    usuario_id = request.session['usuario_id']
    
    try:
        with connection.cursor() as cursor:
            if tipo == 'cancion':
                cursor.execute("""
                    SELECT 1 FROM descargas_offline 
                    WHERE usuario_id = %s AND cancion_id = %s AND tipo = 'cancion'
                """, [usuario_id, item_id])
            elif tipo == 'album':
                cursor.execute("""
                    SELECT 1 FROM descargas_offline 
                    WHERE usuario_id = %s AND album_id = %s AND tipo = 'album'
                """, [usuario_id, item_id])
            elif tipo == 'playlist':
                cursor.execute("""
                    SELECT 1 FROM descargas_offline 
                    WHERE usuario_id = %s AND playlist_id = %s AND tipo = 'playlist'
                """, [usuario_id, item_id])
            else:
                return JsonResponse({'success': False})
            
            descargado = cursor.fetchone() is not None
            
            return JsonResponse({
                'success': True,
                'descargado': descargado
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
@csrf_exempt
def actualizar_portada_playlist(request):
    """Actualizar la imagen de portada de una playlist"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    usuario_id = request.session['usuario_id']
    
    try:
        playlist_id = request.POST.get('playlist_id')
        
        # Verificar que la playlist pertenece al usuario
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nombre FROM playlists 
                WHERE playlist_id = %s AND usuario_id = %s
            """, [playlist_id, usuario_id])
            
            if not cursor.fetchone():
                return JsonResponse({'success': False, 'message': 'Playlist no encontrada'})
        
        # Verificar si se subió una imagen
        if 'imagen' in request.FILES:
            imagen = request.FILES['imagen']
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if imagen.content_type not in allowed_types:
                return JsonResponse({'success': False, 'message': 'Tipo de archivo no permitido. Usa JPG, PNG, GIF o WEBP'})
            
            # Validar tamaño (máximo 5MB)
            if imagen.size > 5 * 1024 * 1024:
                return JsonResponse({'success': False, 'message': 'La imagen es muy grande (máx. 5MB)'})
            
            # Crear directorio si no existe
            import os
            from django.conf import settings
            
            upload_dir = os.path.join(settings.BASE_DIR, 'interfaz', 'static', 'interfaz', 'imagenes', 'playlists')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar nombre único
            import time
            ext = imagen.name.split('.')[-1].lower()
            filename = f"playlist_{playlist_id}_{int(time.time())}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            
            # Guardar archivo
            with open(filepath, 'wb+') as destination:
                for chunk in imagen.chunks():
                    destination.write(chunk)
            
            # Ruta para guardar en BD
            imagen_path = f"/static/interfaz/imagenes/playlists/{filename}"
            
        elif 'imagen_predeterminada' in request.POST:
            # Usar imagen predeterminada seleccionada
            imagen_path = request.POST.get('imagen_predeterminada')
        else:
            return JsonResponse({'success': False, 'message': 'No se proporcionó imagen'})
        
        # Actualizar en BD
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE playlists 
                SET imagen_portada = %s 
                WHERE playlist_id = %s AND usuario_id = %s
            """, [imagen_path, playlist_id, usuario_id])
        
        return JsonResponse({
            'success': True,
            'message': 'Portada actualizada correctamente',
            'nueva_portada': imagen_path
        })
        
    except Exception as e:
        print(f"Error al actualizar portada: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def toggle_visibilidad_playlist(request):
    """Cambiar visibilidad de playlist (pública/privada)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Obtener estado actual
            cursor.execute("""
                SELECT es_publica, nombre FROM playlists 
                WHERE playlist_id = %s AND usuario_id = %s
            """, [playlist_id, usuario_id])
            
            resultado = cursor.fetchone()
            if not resultado:
                return JsonResponse({'success': False, 'message': 'Playlist no encontrada'})
            
            estado_actual = resultado[0]
            nombre_playlist = resultado[1]
            
            # Toggle: si es 1 pasa a 0, si es 0 pasa a 1
            nuevo_estado = 0 if estado_actual == 1 else 1
            
            cursor.execute("""
                UPDATE playlists 
                SET es_publica = %s 
                WHERE playlist_id = %s AND usuario_id = %s
            """, [nuevo_estado, playlist_id, usuario_id])
        
        return JsonResponse({
            'success': True,
            'es_publica': nuevo_estado == 1,
            'message': f'"{nombre_playlist}" ahora es {"pública 🌐" if nuevo_estado == 1 else "privada 🔒"}'
        })
        
    except Exception as e:
        print(f"Error al cambiar visibilidad: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def renombrar_playlist(request):
    """Cambiar nombre de una playlist"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        nuevo_nombre = data.get('nombre', '').strip()
        usuario_id = request.session['usuario_id']
        
        if not nuevo_nombre:
            return JsonResponse({'success': False, 'message': 'El nombre no puede estar vacío'})
        
        if len(nuevo_nombre) > 30:
            return JsonResponse({'success': False, 'message': 'El nombre es muy largo (máx. 30 caracteres)'})
        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE playlists 
                SET nombre = %s 
                WHERE playlist_id = %s AND usuario_id = %s
            """, [nuevo_nombre, playlist_id, usuario_id])
            
            if cursor.rowcount == 0:
                return JsonResponse({'success': False, 'message': 'Playlist no encontrada'})
        
        return JsonResponse({
            'success': True,
            'message': 'Nombre actualizado correctamente',
            'nuevo_nombre': nuevo_nombre
        })
        
    except Exception as e:
        print(f"Error al renombrar: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def eliminar_playlist(request):
    """Eliminar una playlist"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar propiedad y obtener nombre
            cursor.execute("""
                SELECT nombre FROM playlists 
                WHERE playlist_id = %s AND usuario_id = %s
            """, [playlist_id, usuario_id])
            
            resultado = cursor.fetchone()
            if not resultado:
                return JsonResponse({'success': False, 'message': 'Playlist no encontrada'})
            
            nombre_playlist = resultado[0]
            
            # Eliminar canciones de la playlist primero (integridad referencial)
            cursor.execute("""
                DELETE FROM playlists_canciones WHERE playlist_id = %s
            """, [playlist_id])
            
            # Eliminar de descargas offline si existe
            cursor.execute("""
                DELETE FROM descargas_offline WHERE playlist_id = %s
            """, [playlist_id])
            
            # Eliminar la playlist
            cursor.execute("""
                DELETE FROM playlists WHERE playlist_id = %s AND usuario_id = %s
            """, [playlist_id, usuario_id])
        
        return JsonResponse({
            'success': True,
            'message': f'Playlist "{nombre_playlist}" eliminada correctamente',
            'redirect': True
        })
        
    except Exception as e:
        print(f"Error al eliminar: {e}")
        return JsonResponse({'success': False, 'message': str(e)})

def perfil_usuario(request):
    """Ver perfil del usuario logueado"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    usuario = None
    redes = []
    mis_canciones = []
    cancion_anthem = None
    todas_canciones = []
    mis_resenas = []
    
    try:
        with connection.cursor() as cursor:
            # =========================================================
            # A. DATOS DEL USUARIO
            # =========================================================
            cursor.execute("""
                SELECT 
                    u.usuario_id, 
                    u.nombre, 
                    u.apellido, 
                    u.email, 
                    u.descripcion, 
                    u.foto_perfil_path, 
                    u.cancion_id, 
                    CASE WHEN a.usuario_id IS NOT NULL THEN 1 ELSE 0 END as es_artista
                FROM usuarios u
                LEFT JOIN artistas a ON u.usuario_id = a.usuario_id
                WHERE u.usuario_id = %s
            """, [usuario_id])
            
            row = cursor.fetchone()
            if row:
                usuario = {
                    'usuario_id': row[0],
                    'nombre': row[1] or '',
                    'apellido': row[2] or '',
                    'email': row[3] or '',
                    'descripcion': row[4] or '',
                    'foto_perfil_path': row[5] or '',
                    'cancion_id': row[6],
                    'es_artista': row[7] == 1
                }
            
            # =========================================================
            # B. REDES SOCIALES (compatible con cualquier nombre de PK)
            # =========================================================
            try:
                cursor.execute("""
                    SELECT * FROM redes_sociales
                    WHERE usuario_id = %s
                """, [usuario_id])
                
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        row_dict = dict(zip(columns, row))
                        # Buscar el ID (puede ser 'id', 'red_social_id', etc.)
                        pk_value = row_dict.get('red_social_id') or row_dict.get('id') or 0
                        redes.append({
                            'pk': pk_value,
                            'nombre_red': row_dict.get('nombre_red', ''),
                            'url': row_dict.get('url', '')
                        })
            except Exception as e:
                print(f"⚠️ Redes sociales: {e}")
                redes = []
            
            # =========================================================
            # C. MIS PUBLICACIONES (canciones del artista)
            # =========================================================
            try:
                cursor.execute("""
                    SELECT c.cancion_id, c.titulo, c.duracion
                    FROM canciones c
                    INNER JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id
                    INNER JOIN artistas a ON ca.artista_id = a.artista_id
                    WHERE a.usuario_id = %s
                    ORDER BY c.cancion_id DESC
                    LIMIT 10
                """, [usuario_id])
                
                for row in cursor.fetchall():
                    duracion = str(row[2]) if row[2] else "0:00"
                    if len(duracion) > 5:
                        duracion = duracion[3:8]
                    mis_canciones.append({
                        'cancion_id': row[0],
                        'titulo': row[1] or 'Sin título',
                        'duracion': duracion
                    })
            except Exception as e:
                print(f"⚠️ Mis canciones: {e}")
                mis_canciones = []
            
            # =========================================================
            # D. MIS RESEÑAS
            # =========================================================
            try:
                cursor.execute("""
                    SELECT 
                        r.resena_cancion_id,
                        r.comentario,
                        r.puntuacion_estrellas,
                        r.fecha_resena,
                        c.cancion_id,
                        c.titulo as cancion_titulo,
                        a.imagen_portada_path as portada
                    FROM resenas_canciones r
                    JOIN canciones c ON r.cancion_id = c.cancion_id
                    LEFT JOIN albumes a ON c.album_id = a.album_id
                    WHERE r.usuario_id = %s
                    ORDER BY r.fecha_resena DESC
                    LIMIT 20
                """, [usuario_id])
                
                for row in cursor.fetchall():
                    mis_resenas.append({
                        'id': row[0],
                        'comentario': row[1] or '',
                        'rating': row[2] or 0,
                        'fecha': row[3],
                        'cancion_id': row[4],
                        'cancion_titulo': row[5] or 'Sin título',
                        'portada': row[6] or 'https://via.placeholder.com/80?text=Song'
                    })
                print(f"✅ Reseñas encontradas: {len(mis_resenas)}")
            except Exception as e:
                print(f"⚠️ Mis reseñas: {e}")
                mis_resenas = []
            
            # =========================================================
            # E. CANCIÓN ANTHEM (Himno del perfil)
            # =========================================================
            if usuario and usuario['cancion_id']:
                try:
                    cursor.execute("""
                        SELECT c.cancion_id, c.titulo, c.ruta_archivo, 
                               a.imagen_portada_path, ar.nombre as artista
                        FROM canciones c
                        LEFT JOIN albumes a ON c.album_id = a.album_id
                        LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id 
                            AND ca.tipo_participacion = 'Principal'
                        LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                        WHERE c.cancion_id = %s
                    """, [usuario['cancion_id']])
                    
                    row = cursor.fetchone()
                    if row:
                        cancion_anthem = {
                            'cancion_id': row[0],
                            'titulo': row[1] or 'Sin título',
                            'ruta_archivo': row[2],
                            'portada': row[3] or 'https://via.placeholder.com/80?text=Song',
                            'artista': row[4] or 'Artista desconocido'
                        }
                except Exception as e:
                    print(f"⚠️ Anthem: {e}")
            
            # =========================================================
            # F. TODAS LAS CANCIONES (Para buscador de anthem)
            # =========================================================
            try:
                cursor.execute("""
                    SELECT c.cancion_id, c.titulo, ar.nombre as artista
                    FROM canciones c
                    LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id 
                        AND ca.tipo_participacion = 'Principal'
                    LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                    ORDER BY c.titulo
                    LIMIT 500
                """)
                
                for row in cursor.fetchall():
                    todas_canciones.append({
                        'cancion_id': row[0],
                        'titulo': row[1] or 'Sin título',
                        'artista': row[2] or 'Artista desconocido'
                    })
            except Exception as e:
                print(f"⚠️ Todas canciones: {e}")
                
    except Exception as e:
        print(f"❌ Error general en perfil_usuario: {e}")
        import traceback
        traceback.print_exc()
    
    if not usuario:
        messages.error(request, 'Error al cargar el perfil')
        return redirect('lista_reproduccion')
    
    context = {
        'usuario': usuario,
        'redes': redes,
        'mis_canciones': mis_canciones,
        'cancion_anthem': cancion_anthem,
        'todas_canciones': todas_canciones,
        'mis_resenas': mis_resenas
    }
    
    return render(request, 'interfaz/perfil_usuario.html', context)

@csrf_exempt
def editar_perfil(request):
    """Editar perfil del usuario"""
    if request.method != 'POST':
        return redirect('perfil_usuario')
    
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    
    try:
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        cancion_anthem_id = request.POST.get('cancion_anthem_id', '').strip()
        eliminar_foto = request.POST.get('eliminar_foto')
        
        # Nueva red social
        nueva_red_nombre = request.POST.get('nueva_red_nombre', '').strip()
        nueva_red_url = request.POST.get('nueva_red_url', '').strip()
        
        with connection.cursor() as cursor:
            # Manejar foto de perfil
            foto_path = None
            
            if eliminar_foto:
                foto_path = ''
            elif 'foto_perfil' in request.FILES:
                import os
                import time
                from django.conf import settings
                
                foto = request.FILES['foto_perfil']
                
                # Validar tipo
                allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if foto.content_type not in allowed_types:
                    messages.error(request, 'Tipo de imagen no permitido')
                    return redirect('perfil_usuario')
                
                # Validar tamaño (5MB)
                if foto.size > 5 * 1024 * 1024:
                    messages.error(request, 'La imagen es muy grande (máx. 5MB)')
                    return redirect('perfil_usuario')
                
                # Crear directorio
                upload_dir = os.path.join(settings.BASE_DIR, 'interfaz', 'static', 'interfaz', 'imagenes', 'perfiles')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Guardar archivo
                ext = foto.name.split('.')[-1].lower()
                filename = f"perfil_{usuario_id}_{int(time.time())}.{ext}"
                filepath = os.path.join(upload_dir, filename)
                
                with open(filepath, 'wb+') as destination:
                    for chunk in foto.chunks():
                        destination.write(chunk)
                
                foto_path = f"/static/interfaz/imagenes/perfiles/{filename}"
            
            # Construir query de actualización
            if foto_path is not None:
                cursor.execute("""
                    UPDATE usuarios 
                    SET nombre = %s, apellido = %s, descripcion = %s, 
                        foto_perfil_path = %s, cancion_id = %s
                    WHERE usuario_id = %s
                """, [nombre, apellido, descripcion, foto_path, 
                      cancion_anthem_id if cancion_anthem_id else None, usuario_id])
            else:
                cursor.execute("""
                    UPDATE usuarios 
                    SET nombre = %s, apellido = %s, descripcion = %s, cancion_id = %s
                    WHERE usuario_id = %s
                """, [nombre, apellido, descripcion, 
                      cancion_anthem_id if cancion_anthem_id else None, usuario_id])
            
            # Agregar nueva red social si se proporcionó
            if nueva_red_nombre and nueva_red_url:
                cursor.execute("""
                    INSERT INTO redes_sociales (usuario_id, nombre_red, url)
                    VALUES (%s, %s, %s)
                """, [usuario_id, nueva_red_nombre, nueva_red_url])
            
            # Actualizar nombre en sesión
            request.session['usuario_nombre'] = nombre
        
        messages.success(request, 'Perfil actualizado correctamente')
        
    except Exception as e:
        print(f"Error al editar perfil: {e}")
        messages.error(request, f'Error al actualizar: {str(e)}')
    
    return redirect('perfil_usuario')


def eliminar_red_social(request, red_id):
    """Eliminar una red social del perfil"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM redes_sociales 
                WHERE red_social_id = %s AND usuario_id = %s
            """, [red_id, usuario_id])
        
        messages.success(request, 'Red social eliminada')
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, 'Error al eliminar')
    
    return redirect('perfil_usuario')


# ============== COMPARTIR CANCIÓN ==============

def compartir_cancion(request, cancion_id):
    """Vista para compartir una canción (requiere login)"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    cancion = None
    artista = ''
    portada = ''
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.cancion_id, c.titulo, c.ruta_archivo, c.duracion,
                       a.imagen_portada_path, ar.nombre as artista
                FROM canciones c
                LEFT JOIN albumes a ON c.album_id = a.album_id
                LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id 
                    AND ca.tipo_participacion = 'Principal'
                LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                WHERE c.cancion_id = %s
            """, [cancion_id])
            
            row = cursor.fetchone()
            if row:
                duracion = str(row[3]) if row[3] else "0:00"
                if len(duracion) > 5:
                    duracion = duracion[3:8]
                
                cancion = {
                    'id': row[0],
                    'titulo': row[1] or 'Sin título',
                    'ruta_archivo': row[2],
                    'duracion': duracion
                }
                portada = row[4] or 'https://via.placeholder.com/250?text=Song'
                artista = row[5] or 'Artista desconocido'
                
    except Exception as e:
        print(f"Error en compartir_cancion: {e}")
    
    if not cancion:
        messages.error(request, 'Canción no encontrada')
        return redirect('lista_reproduccion')
    
    # Generar URL para compartir
    share_url = request.build_absolute_uri()
    
    context = {
        'cancion': cancion,
        'artista': artista,
        'portada': portada,
        'share_url': share_url
    }
    
    return render(request, 'interfaz/compartir_cancion.html', context)
@csrf_exempt
def obtener_resenas_cancion(request, cancion_id):
    """Obtener todas las reseñas de una canción"""
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    usuario_id = request.session['usuario_id']
    resenas = []
    promedio_rating = 0
    total_ratings = 0
    user_rating = 0
    
    try:
        with connection.cursor() as cursor:
            # Obtener reseñas con información del usuario
            cursor.execute("""
                SELECT 
                    r.resena_cancion_id,
                    r.usuario_id,
                    r.comentario,
                    r.puntuacion_estrellas,
                    r.fecha_resena,
                    COALESCE((SELECT COUNT(*) FROM reacciones_resenas_canciones 
                              WHERE resena_cancion_id = r.resena_cancion_id AND tipo = 'like'), 0) as likes,
                    COALESCE((SELECT COUNT(*) FROM reacciones_resenas_canciones 
                              WHERE resena_cancion_id = r.resena_cancion_id AND tipo = 'dislike'), 0) as dislikes,
                    u.nombre,
                    u.apellido,
                    u.foto_perfil_path,
                    (SELECT tipo FROM reacciones_resenas_canciones 
                     WHERE resena_cancion_id = r.resena_cancion_id AND usuario_id = %s LIMIT 1) as user_reaccion
                FROM resenas_canciones r
                JOIN usuarios u ON r.usuario_id = u.usuario_id
                WHERE r.cancion_id = %s
                ORDER BY r.fecha_resena DESC
            """, [usuario_id, cancion_id])
            
            for row in cursor.fetchall():
                fecha_formateada = ''
                if row[4]:
                    try:
                        fecha_formateada = row[4].strftime('%d/%m/%Y')
                    except:
                        fecha_formateada = str(row[4])
                
                resenas.append({
                    'id': row[0],
                    'usuario_id': row[1],
                    'comentario': row[2] or '',
                    'rating': row[3],
                    'fecha': fecha_formateada,
                    'likes': row[5] or 0,
                    'dislikes': row[6] or 0,
                    'nombre': row[7] or 'Usuario',
                    'apellido': row[8] or '',
                    'foto_perfil': row[9] or '',
                    'user_liked': row[10] == 'like' if row[10] else False,
                    'user_disliked': row[10] == 'dislike' if row[10] else False
                })
            
            # Calcular promedio de ratings
            cursor.execute("""
                SELECT AVG(puntuacion_estrellas), COUNT(puntuacion_estrellas)
                FROM resenas_canciones
                WHERE cancion_id = %s AND puntuacion_estrellas IS NOT NULL
            """, [cancion_id])
            
            result = cursor.fetchone()
            if result:
                promedio_rating = float(result[0]) if result[0] else 0
                total_ratings = result[1] or 0
            
            # Obtener rating del usuario actual
            cursor.execute("""
                SELECT puntuacion_estrellas FROM resenas_canciones
                WHERE cancion_id = %s AND usuario_id = %s
            """, [cancion_id, usuario_id])
            
            user_result = cursor.fetchone()
            if user_result and user_result[0]:
                user_rating = user_result[0]
                
    except Exception as e:
        print(f"Error obteniendo reseñas: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({
        'success': True,
        'resenas': resenas,
        'promedio_rating': round(promedio_rating, 1),
        'total_ratings': total_ratings,
        'user_rating': user_rating
    })


@csrf_exempt
def agregar_resena(request):
    """Agregar o actualizar una reseña"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        cancion_id = data.get('cancion_id')
        comentario = data.get('comentario', '').strip()
        rating = data.get('rating')
        usuario_id = request.session['usuario_id']
        
        # Validaciones
        if not cancion_id:
            return JsonResponse({'success': False, 'message': 'Canción no especificada'})
        
        if rating is not None:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({'success': False, 'message': 'Rating debe ser entre 1 y 5'})
        
        with connection.cursor() as cursor:
            # Verificar si ya existe una reseña del usuario para esta canción
            cursor.execute("""
                SELECT resena_cancion_id, comentario, puntuacion_estrellas 
                FROM resenas_canciones
                WHERE usuario_id = %s AND cancion_id = %s
            """, [usuario_id, cancion_id])
            
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar reseña existente
                if comentario or rating:
                    cursor.execute("""
                        UPDATE resenas_canciones 
                        SET comentario = COALESCE(%s, comentario),
                            puntuacion_estrellas = COALESCE(%s, puntuacion_estrellas),
                            fecha_resena = CURDATE()
                        WHERE usuario_id = %s AND cancion_id = %s
                    """, [comentario if comentario else None, rating, usuario_id, cancion_id])
                    message = 'Reseña actualizada'
                else:
                    message = 'Sin cambios'
            else:
                # Crear nueva reseña
                cursor.execute("""
                    INSERT INTO resenas_canciones 
                    (usuario_id, cancion_id, comentario, puntuacion_estrellas, fecha_resena)
                    VALUES (%s, %s, %s, %s, CURDATE())
                """, [usuario_id, cancion_id, comentario if comentario else None, rating])
                message = 'Reseña publicada'
            
            # Obtener nuevos promedios
            cursor.execute("""
                SELECT AVG(puntuacion_estrellas), COUNT(puntuacion_estrellas)
                FROM resenas_canciones
                WHERE cancion_id = %s AND puntuacion_estrellas IS NOT NULL
            """, [cancion_id])
            
            result = cursor.fetchone()
            promedio = float(result[0]) if result[0] else 0
            total_ratings = result[1] or 0
            
            # Obtener rating del usuario
            cursor.execute("""
                SELECT puntuacion_estrellas FROM resenas_canciones
                WHERE cancion_id = %s AND usuario_id = %s
            """, [cancion_id, usuario_id])
            
            user_result = cursor.fetchone()
            user_rating = user_result[0] if user_result and user_result[0] else 0
        
        return JsonResponse({
            'success': True,
            'message': message,
            'promedio_rating': round(promedio, 1),
            'total_ratings': total_ratings,
            'user_rating': user_rating
        })
        
    except Exception as e:
        print(f"Error al agregar reseña: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def eliminar_resena(request):
    """Eliminar una reseña propia"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        resena_id = data.get('resena_id')
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar que la reseña pertenece al usuario
            cursor.execute("""
                SELECT cancion_id FROM resenas_canciones
                WHERE resena_cancion_id = %s AND usuario_id = %s
            """, [resena_id, usuario_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'success': False, 'message': 'No puedes eliminar esta reseña'})
            
            cancion_id = result[0]
            
            # Eliminar reacciones asociadas primero
            cursor.execute("""
                DELETE FROM reacciones_resenas_canciones WHERE resena_cancion_id = %s
            """, [resena_id])
            
            # Eliminar la reseña
            cursor.execute("""
                DELETE FROM resenas_canciones WHERE resena_cancion_id = %s AND usuario_id = %s
            """, [resena_id, usuario_id])
        
        return JsonResponse({
            'success': True,
            'message': 'Reseña eliminada',
            'cancion_id': cancion_id
        })
        
    except Exception as e:
        print(f"Error al eliminar reseña: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def reaccionar_resena(request):
    """Like o dislike a una reseña"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        resena_id = data.get('resena_id')
        tipo = data.get('tipo')  # 'like' o 'dislike'
        usuario_id = request.session['usuario_id']
        
        if tipo not in ['like', 'dislike']:
            return JsonResponse({'success': False, 'message': 'Tipo de reacción inválido'})
        
        with connection.cursor() as cursor:
            # Verificar si ya existe una reacción
            cursor.execute("""
                SELECT tipo FROM reacciones_resenas_canciones
                WHERE usuario_id = %s AND resena_cancion_id = %s
            """, [usuario_id, resena_id])
            
            existing = cursor.fetchone()
            reaccion_usuario = None
            
            if existing:
                if existing[0] == tipo:
                    # Mismo tipo: eliminar reacción (toggle off)
                    cursor.execute("""
                        DELETE FROM reacciones_resenas_canciones
                        WHERE usuario_id = %s AND resena_cancion_id = %s
                    """, [usuario_id, resena_id])
                    reaccion_usuario = None
                else:
                    # Diferente tipo: cambiar reacción
                    cursor.execute("""
                        UPDATE reacciones_resenas_canciones SET tipo = %s
                        WHERE usuario_id = %s AND resena_cancion_id = %s
                    """, [tipo, usuario_id, resena_id])
                    reaccion_usuario = tipo
            else:
                # Nueva reacción
                cursor.execute("""
                    INSERT INTO reacciones_resenas_canciones (usuario_id, resena_cancion_id, tipo)
                    VALUES (%s, %s, %s)
                """, [usuario_id, resena_id, tipo])
                reaccion_usuario = tipo
            
            # Obtener contadores actualizados
            cursor.execute("""
                SELECT 
                    COALESCE((SELECT COUNT(*) FROM reacciones_resenas_canciones 
                              WHERE resena_cancion_id = %s AND tipo = 'like'), 0),
                    COALESCE((SELECT COUNT(*) FROM reacciones_resenas_canciones 
                              WHERE resena_cancion_id = %s AND tipo = 'dislike'), 0)
            """, [resena_id, resena_id])
            
            counts = cursor.fetchone()
        
        return JsonResponse({
            'success': True,
            'likes': counts[0] if counts else 0,
            'dislikes': counts[1] if counts else 0,
            'reaccion_usuario': reaccion_usuario
        })
        
    except Exception as e:
        print(f"Error al reaccionar: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def solicitar_artista(request):
    """Solicitar verificación como artista"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        nombre_artistico = data.get('nombre_artistico', '').strip()
        biografia = data.get('biografia', '').strip()
        genero_principal = data.get('genero_principal', '').strip()
        redes_sociales = data.get('redes_sociales', '').strip()
        usuario_id = request.session['usuario_id']
        
        if not nombre_artistico:
            return JsonResponse({'success': False, 'message': 'El nombre artístico es obligatorio'})
        
        with connection.cursor() as cursor:
            # Verificar si ya tiene una solicitud pendiente
            cursor.execute("""
                SELECT estado FROM solicitudes_artista 
                WHERE usuario_id = %s AND estado = 'pendiente'
            """, [usuario_id])
            
            if cursor.fetchone():
                return JsonResponse({'success': False, 'message': 'Ya tienes una solicitud pendiente'})
            
            # Verificar si ya es artista
            cursor.execute("""
                SELECT es_artista FROM usuarios WHERE usuario_id = %s
            """, [usuario_id])
            
            result = cursor.fetchone()
            if result and result[0] == 1:
                return JsonResponse({'success': False, 'message': 'Ya eres un artista verificado'})
            
            # Crear solicitud
            cursor.execute("""
                INSERT INTO solicitudes_artista 
                (usuario_id, nombre_artistico, biografia, genero_principal, redes_sociales, estado, fecha_solicitud)
                VALUES (%s, %s, %s, %s, %s, 'pendiente', NOW())
            """, [usuario_id, nombre_artistico, biografia, genero_principal, redes_sociales])
        
        return JsonResponse({
            'success': True,
            'message': '¡Solicitud enviada! Te notificaremos cuando sea revisada.'
        })
        
    except Exception as e:
        print(f"Error al solicitar artista: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


def subir_album(request):
    """Vista para subir un álbum (solo artistas)"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    
    # Verificar si es artista
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT es_artista, nombre FROM usuarios WHERE usuario_id = %s
            """, [usuario_id])
            result = cursor.fetchone()
            
            if not result or result[0] != 1:
                messages.error(request, 'Debes ser un artista verificado para subir música')
                return redirect('perfil_usuario')
            
            usuario_nombre = result[1]
    except Exception as e:
        messages.error(request, 'Error al verificar permisos')
        return redirect('perfil_usuario')
    
    if request.method == 'POST':
        # Procesar subida de álbum
        titulo_album = request.POST.get('titulo_album', '').strip()
        
        if not titulo_album:
            messages.error(request, 'El título del álbum es obligatorio')
            return render(request, 'interfaz/subir_album.html', {'usuario_nombre': usuario_nombre})
        
        try:
            # Aquí iría la lógica para guardar el álbum y las canciones
            # Por ahora solo mostramos mensaje de éxito
            messages.success(request, f'Álbum "{titulo_album}" subido correctamente')
            return redirect('perfil_usuario')
            
        except Exception as e:
            messages.error(request, f'Error al subir álbum: {str(e)}')
    
    return render(request, 'interfaz/subir_album.html', {'usuario_nombre': usuario_nombre})

@csrf_exempt
def solicitar_artista(request):
    """Solicitar verificación como artista"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        nombre_artistico = data.get('nombre_artistico', '').strip()
        biografia = data.get('biografia', '').strip()
        genero_principal = data.get('genero_principal', '').strip()
        redes_sociales = data.get('redes_sociales', '').strip()
        usuario_id = request.session['usuario_id']
        
        if not nombre_artistico:
            return JsonResponse({'success': False, 'message': 'El nombre artístico es obligatorio'})
        
        with connection.cursor() as cursor:
            # Verificar si ya tiene una solicitud pendiente
            cursor.execute("""
                SELECT estado FROM solicitudes_artista 
                WHERE usuario_id = %s AND estado = 'pendiente'
            """, [usuario_id])
            
            if cursor.fetchone():
                return JsonResponse({'success': False, 'message': 'Ya tienes una solicitud pendiente'})
            
            # Verificar si ya es artista
            cursor.execute("""
                SELECT es_artista FROM usuarios WHERE usuario_id = %s
            """, [usuario_id])
            
            result = cursor.fetchone()
            if result and result[0] == 1:
                return JsonResponse({'success': False, 'message': 'Ya eres un artista verificado'})
            
            # Crear solicitud
            cursor.execute("""
                INSERT INTO solicitudes_artista 
                (usuario_id, nombre_artistico, biografia, genero_principal, redes_sociales, estado, fecha_solicitud)
                VALUES (%s, %s, %s, %s, %s, 'pendiente', NOW())
            """, [usuario_id, nombre_artistico, biografia, genero_principal, redes_sociales])
        
        return JsonResponse({
            'success': True,
            'message': '¡Solicitud enviada! Te notificaremos cuando sea revisada.'
        })
        
    except Exception as e:
        print(f"Error al solicitar artista: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


# ============== SUBIR ÁLBUM (ARTISTAS) ==============

def subir_album(request):
    """Vista para subir un álbum (solo artistas verificados)"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    generos = []
    
    try:
        with connection.cursor() as cursor:
            # Verificar si es artista
            cursor.execute("""
                SELECT es_artista, nombre FROM usuarios WHERE usuario_id = %s
            """, [usuario_id])
            result = cursor.fetchone()
            
            if not result or result[0] != 1:
                messages.error(request, 'Debes ser un artista verificado para subir música')
                return redirect('perfil_usuario')
            
            usuario_nombre = result[1]
            
            # Obtener géneros disponibles
            cursor.execute("SELECT genero_id, nombre FROM generos ORDER BY nombre")
            for row in cursor.fetchall():
                generos.append({'genero_id': row[0], 'nombre': row[1]})
                
    except Exception as e:
        messages.error(request, 'Error al verificar permisos')
        return redirect('perfil_usuario')
    
    if request.method == 'POST':
        titulo_album = request.POST.get('titulo_album', '').strip()
        genero_id = request.POST.get('genero_global')
        permitir_descarga = 1 if request.POST.get('permitir_descarga') else 0
        
        nombres_canciones = request.POST.getlist('nombre_cancion[]')
        archivos_canciones = request.FILES.getlist('archivo_cancion[]')
        portada = request.FILES.get('portada_album')
        
        if not titulo_album:
            messages.error(request, 'El título del álbum es obligatorio')
            return render(request, 'interfaz/subir_album.html', {
                'usuario_nombre': usuario_nombre,
                'generos': generos
            })
        
        try:
            import os
            import time
            from django.conf import settings
            
            # Crear directorios si no existen
            portadas_dir = os.path.join(settings.BASE_DIR, 'interfaz', 'static', 'interfaz', 'imagenes', 'albumes')
            canciones_dir = os.path.join(settings.BASE_DIR, 'interfaz', 'static', 'interfaz', 'audio')
            os.makedirs(portadas_dir, exist_ok=True)
            os.makedirs(canciones_dir, exist_ok=True)
            
            # Guardar portada
            portada_path = None
            if portada:
                ext = portada.name.split('.')[-1].lower()
                portada_filename = f"album_{usuario_id}_{int(time.time())}.{ext}"
                portada_filepath = os.path.join(portadas_dir, portada_filename)
                
                with open(portada_filepath, 'wb+') as f:
                    for chunk in portada.chunks():
                        f.write(chunk)
                
                portada_path = f"/static/interfaz/imagenes/albumes/{portada_filename}"
            
            with connection.cursor() as cursor:
                # Obtener o crear artista_id del usuario
                cursor.execute("""
                    SELECT artista_id FROM artistas WHERE usuario_id = %s
                """, [usuario_id])
                artista_result = cursor.fetchone()
                
                if not artista_result:
                    cursor.execute("""
                        INSERT INTO artistas (nombre, usuario_id)
                        VALUES (%s, %s)
                    """, [usuario_nombre, usuario_id])
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    artista_id = cursor.fetchone()[0]
                else:
                    artista_id = artista_result[0]
                
                # Crear álbum
                cursor.execute("""
                    INSERT INTO albumes (titulo, imagen_portada_path, fecha_lanzamiento, permitir_descarga)
                    VALUES (%s, %s, CURDATE(), %s)
                """, [titulo_album, portada_path, permitir_descarga])
                
                cursor.execute("SELECT LAST_INSERT_ID()")
                album_id = cursor.fetchone()[0]
                
                # Vincular álbum con artista
                cursor.execute("""
                    INSERT INTO albumes_artistas (album_id, artista_id, rol)
                    VALUES (%s, %s, 'Principal')
                """, [album_id, artista_id])
                
                # Guardar canciones
                for i, (nombre, archivo) in enumerate(zip(nombres_canciones, archivos_canciones)):
                    if not nombre.strip() or not archivo:
                        continue
                    
                    # Guardar archivo de audio
                    ext = archivo.name.split('.')[-1].lower()
                    audio_filename = f"cancion_{album_id}_{i+1}_{int(time.time())}.{ext}"
                    audio_filepath = os.path.join(canciones_dir, audio_filename)
                    
                    with open(audio_filepath, 'wb+') as f:
                        for chunk in archivo.chunks():
                            f.write(chunk)
                    
                    audio_path = f"/static/interfaz/audio/{audio_filename}"
                    
                    # Insertar canción
                    cursor.execute("""
                        INSERT INTO canciones (album_id, titulo, ruta_archivo, permitir_descarga)
                        VALUES (%s, %s, %s, %s)
                    """, [album_id, nombre.strip(), audio_path, permitir_descarga])
                    
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    cancion_id = cursor.fetchone()[0]
                    
                    # Vincular canción con artista
                    cursor.execute("""
                        INSERT INTO canciones_artistas (cancion_id, artista_id, tipo_participacion)
                        VALUES (%s, %s, 'Principal')
                    """, [cancion_id, artista_id])
                    
                    # Vincular canción con género
                    if genero_id:
                        cursor.execute("""
                            INSERT INTO canciones_generos (cancion_id, genero_id)
                            VALUES (%s, %s)
                        """, [cancion_id, genero_id])
            
            messages.success(request, f'¡Álbum "{titulo_album}" publicado exitosamente!')
            return redirect('perfil_usuario')
            
        except Exception as e:
            print(f"Error al subir álbum: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error al subir álbum: {str(e)}')
    
    return render(request, 'interfaz/subir_album.html', {
        'usuario_nombre': usuario_nombre,
        'generos': generos
    })


# ============== PANEL ADMIN ARTISTAS ==============

def panel_admin_artistas(request):
    """Panel de administración para solicitudes de artistas"""
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session['usuario_id']
    
    try:
        with connection.cursor() as cursor:
            # Verificar si es admin
            cursor.execute("""
                SELECT es_admin, nombre FROM usuarios WHERE usuario_id = %s
            """, [usuario_id])
            result = cursor.fetchone()
            
            if not result or result[0] != 1:
                messages.error(request, 'No tienes permisos de administrador')
                return redirect('lista_reproduccion')
            
            usuario = {'nombre': result[1]}
            
            # Procesar acciones POST
            if request.method == 'POST':
                solicitud_id = request.POST.get('solicitud_id')
                accion = request.POST.get('accion')
                
                if solicitud_id and accion:
                    if accion == 'aprobar':
                        # Obtener usuario de la solicitud
                        cursor.execute("""
                            SELECT usuario_id, nombre_artistico FROM solicitudes_artista WHERE solicitud_id = %s
                        """, [solicitud_id])
                        sol_data = cursor.fetchone()
                        
                        if sol_data:
                            sol_user_id = sol_data[0]
                            nombre_artistico = sol_data[1]
                            
                            # Actualizar usuario como artista
                            cursor.execute("""
                                UPDATE usuarios SET es_artista = 1 WHERE usuario_id = %s
                            """, [sol_user_id])
                            
                            # Crear entrada en tabla artistas si no existe
                            cursor.execute("""
                                SELECT artista_id FROM artistas WHERE usuario_id = %s
                            """, [sol_user_id])
                            
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO artistas (nombre, usuario_id)
                                    VALUES (%s, %s)
                                """, [nombre_artistico, sol_user_id])
                            
                            # Actualizar estado de solicitud
                            cursor.execute("""
                                UPDATE solicitudes_artista 
                                SET estado = 'aprobada', fecha_respuesta = NOW()
                                WHERE solicitud_id = %s
                            """, [solicitud_id])
                            
                            messages.success(request, f'Solicitud aprobada. {nombre_artistico} ahora es artista.')
                    
                    elif accion == 'rechazar':
                        cursor.execute("""
                            UPDATE solicitudes_artista 
                            SET estado = 'rechazada', fecha_respuesta = NOW()
                            WHERE solicitud_id = %s
                        """, [solicitud_id])
                        messages.success(request, 'Solicitud rechazada.')
            
            # Obtener solicitudes pendientes
            cursor.execute("""
                SELECT 
                    s.solicitud_id,
                    s.nombre_artistico,
                    s.biografia,
                    s.genero_principal,
                    s.redes_sociales,
                    s.fecha_solicitud,
                    u.usuario_id,
                    u.nombre,
                    u.email,
                    u.foto_perfil_path
                FROM solicitudes_artista s
                JOIN usuarios u ON s.usuario_id = u.usuario_id
                WHERE s.estado = 'pendiente'
                ORDER BY s.fecha_solicitud ASC
            """)
            
            solicitudes = []
            for row in cursor.fetchall():
                solicitudes.append({
                    'id': row[0],
                    'nombre_artistico': row[1],
                    'mensaje_motivo': row[2] or 'Sin descripción',
                    'genero': row[3],
                    'enlace_demo': row[4] or '#',
                    'fecha_solicitud': row[5],
                    'usuario': {
                        'id': row[6],
                        'nombre': row[7],
                        'email': row[8],
                        'foto_perfil_path': row[9]
                    }
                })
                
    except Exception as e:
        print(f"Error en panel admin: {e}")
        messages.error(request, 'Error al cargar el panel')
        return redirect('lista_reproduccion')
    
    return render(request, 'interfaz/panel_admin_artistas.html', {
        'usuario': usuario,
        'solicitudes': solicitudes
    })
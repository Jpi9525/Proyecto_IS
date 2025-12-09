
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.db import connection
from .models import Usuario, Generos  # Asegúrate de importar ambos
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
        # Obtener los datos del formulario con los nombres correctos
        username_or_email = request.POST.get('userName') or request.POST.get('email')
        password = request.POST.get('passWord') or request.POST.get('password')
        
        print(f"Datos recibidos - Usuario: {username_or_email}, Password: {password}")  # Debug
        print(f"Todos los datos POST: {request.POST}")  # Ver todos los campos
        
        # Validar que los campos no estén vacíos
        if not username_or_email or not password:
            messages.error(request, 'Por favor ingresa usuario/email y contraseña')
            return render(request, 'interfaz/LoginScreen.html')
        
        try:
            # Buscar usuario - primero verificar si es email
            if '@' in str(username_or_email):  # Convertir a string por si acaso
                usuario = Usuario.objects.get(email=username_or_email)
            else:
                # Buscar por nombre
                usuario = Usuario.objects.get(nombre=username_or_email)
            
            print(f"Usuario encontrado: {usuario.nombre}")
            print(f"Contraseña en BD: '{usuario.contrasena}'")
            print(f"Contraseña ingresada: '{password}'")
            
            # Verificar contraseña
            if usuario.contrasena == password:
                # Login exitoso
                request.session['usuario_id'] = usuario.usuario_id
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_email'] = usuario.email
                
                return redirect('lista_reproduccion')
            else:
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
    
    # Mezclar las canciones
    random.shuffle(todas_las_canciones)
    
    context = {
        'canciones': todas_las_canciones,
        'generos_seleccionados': generos_seleccionados,
        'total_canciones': len(todas_las_canciones)
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
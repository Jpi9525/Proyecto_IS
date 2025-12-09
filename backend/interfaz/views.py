
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.db import connection
from django.core.files.storage import FileSystemStorage
from .models import Usuario, Generos, Canciones,RedesSociales  # Asegúrate de importar ambos
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
        
        print(f"Datos recibidos - Usuario: {username_or_email}, Password: {password}")
        print(f"Todos los datos POST: {request.POST}")
        
        # Validar que los campos no estén vacíos
        if not username_or_email or not password:
            messages.error(request, 'Por favor ingresa usuario/email y contraseña')
            return render(request, 'interfaz/LoginScreen.html')
        
        try:
            # Buscar usuario - primero verificar si es email
            if '@' in str(username_or_email):
                try:
                    usuario = Usuario.objects.get(email=username_or_email)
                except Usuario.DoesNotExist:
                    messages.error(request, 'No existe una cuenta con ese email')
                    return render(request, 'interfaz/LoginScreen.html')
            else:
                # Buscar por nombre
                try:
                    usuario = Usuario.objects.get(nombre=username_or_email)
                except Usuario.DoesNotExist:
                    messages.error(request, 'No existe una cuenta con ese nombre de usuario')
                    return render(request, 'interfaz/LoginScreen.html')
            
            print(f"✅ Usuario encontrado: ID={usuario.usuario_id}, Nombre={usuario.nombre}")
            print(f"📝 Contraseña en BD: '{usuario.contrasena}'")
            print(f"⌨️ Contraseña ingresada: '{password}'")
            
            # IMPORTANTE: Comparar contraseñas DIRECTAMENTE (sin hash en tu caso)
            if password == usuario.contrasena:
                print(f"✅ Contraseña correcta!")
                # Login exitoso
                request.session['usuario_id'] = usuario.usuario_id
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_email'] = usuario.email
                
                # Verificar si ya tiene géneros seleccionados
                if 'generos_favoritos' in request.session and len(request.session['generos_favoritos']) == 3:
                    return redirect('lista_reproduccion')
                else:
                    return redirect('home')
            else:
                print(f"❌ Contraseña incorrecta")
                messages.error(request, 'Contraseña incorrecta')
                
        except Usuario.DoesNotExist:
            messages.error(request, 'No existe una cuenta con esos datos')
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
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
        
    # Obtener ID del usuario logueado
    uid = request.session.get('usuario_id')
    if not uid: return redirect('login')
    try:
        usuario_actual = Usuario.objects.get(usuario_id=uid)
    except Usuario.DoesNotExist:
        return redirect('login')
    
    generos_seleccionados = request.session.get('generos_favoritos', [])
    if not generos_seleccionados or len(generos_seleccionados) != 3:
        messages.warning(request, 'Primero debes seleccionar 3 géneros musicales')
        return redirect('home')



    todas_las_canciones = []
    
    try:
        # Usar SQL directo para obtener las canciones
        with connection.cursor() as cursor:
            # Query para obtener canciones con sus relaciones, likes/dislikes
            query = """
                SELECT 
                    c.cancion_id,
                    c.titulo,
                    c.duracion,
                    c.ruta_archivo,
                    a.titulo as album,
                    a.imagen_portada_path,
                    ar.nombre as artista,
                    g.nombre as genero,
                    COALESCE(likes.total, 0) as likes,
                    COALESCE(dislikes.total, 0) as dislikes,
                    rc.tipo as reaccion_usuario,
                    COALESCE(ratings.avg_rating, 0) as promedio_rating,
                    COALESCE(ratings.total_ratings, 0) as total_ratings,
                    COALESCE(user_rating.valor, 0) as user_rating
                FROM canciones c
                LEFT JOIN albumes a ON c.album_id = a.album_id
                LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id 
                    AND ca.tipo_participacion = 'Principal'
                LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                LEFT JOIN canciones_generos cg ON c.cancion_id = cg.cancion_id
                LEFT JOIN generos g ON cg.genero_id = g.genero_id
                LEFT JOIN (
                    SELECT cancion_id, COUNT(*) as total 
                    FROM reacciones_canciones 
                    WHERE tipo = 'like' 
                    GROUP BY cancion_id
                ) likes ON c.cancion_id = likes.cancion_id
                LEFT JOIN (
                    SELECT cancion_id, COUNT(*) as total 
                    FROM reacciones_canciones 
                    WHERE tipo = 'dislike' 
                    GROUP BY cancion_id
                ) dislikes ON c.cancion_id = dislikes.cancion_id
                LEFT JOIN reacciones_canciones rc ON c.cancion_id = rc.cancion_id 
                    AND rc.usuario_id = %s
                LEFT JOIN (
                    SELECT 
                        cancion_id, 
                        AVG(valor) as avg_rating,
                        COUNT(*) as total_ratings
                    FROM ratings_canciones 
                    GROUP BY cancion_id
                ) ratings ON c.cancion_id = ratings.cancion_id
                LEFT JOIN ratings_canciones user_rating ON c.cancion_id = user_rating.cancion_id 
                    AND user_rating.usuario_id = %s
                WHERE g.nombre IN (%s, %s, %s)
                ORDER BY RAND()
                LIMIT 10
            """
            # Parámetros: usuario_id para reacción personal, luego los 3 géneros
            params = [uid, uid] + generos_seleccionados
            
            print(f"🔍 Parámetros: {params}")
            print(f"📝 Géneros: {generos_seleccionados}")

            cursor.execute(query, params)
            canciones_db = cursor.fetchall()
            
            print(f"✅ Canciones encontradas: {len(canciones_db)}")
            
            # Convertir resultados a diccionarios
            for cancion in canciones_db:
                # Formatear duración
                duracion = str(cancion[2]) if cancion[2] else "0:00"
                if len(duracion) > 5:
                    duracion = duracion[3:8]  # Tomar solo MM:SS
                
                # Asegurar que la portada tenga URL válida
                portada = cancion[5] if cancion[5] else '/static/interfaz/imagenes/default_cover.png'
                # Si es una ruta relativa, convertirla a URL estática
                if portada.startswith('interfaz/imagenes/'):
                    portada = f'/static/{portada}'
                
                todas_las_canciones.append({
                    'id': cancion[0],
                    'titulo': cancion[1],
                    'duracion': duracion,
                    'ruta_archivo': cancion[3],
                    'album': cancion[4] if cancion[4] else 'Sin álbum',
                    'portada': portada,
                    'artista': cancion[6] if cancion[6] else 'Artista desconocido',
                    'genero': cancion[7] if cancion[7] else 'Sin género',
                    'likes': int(cancion[8]),
                    'dislikes': int(cancion[9]),
                    'reaccion_usuario': cancion[10],  # 'like', 'dislike' o None
                    'promedio_rating': float(cancion[11]),  # promedio de rating
                    'total_ratings': int(cancion[12]),  # total de calificaciones
                    'user_rating': int(cancion[13])  # rating del usuario actual (1-5)
                })
                
        print(f"✅ Se cargaron {len(todas_las_canciones)} canciones reales de la BD")
                
    except Exception as e:
        print(f"❌ Error al obtener canciones de la BD: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Error al cargar las canciones. Por favor, intenta de nuevo.')
        # Si hay error, dejamos la lista vacía - NO agregamos canciones demo
    
    # Verificar si hay suficientes canciones
    if len(todas_las_canciones) == 0:
        messages.warning(request, 'No hay canciones disponibles en los géneros seleccionados')
        print("⚠️ No se encontraron canciones en los géneros:", generos_seleccionados)
    
    # Mezclar las canciones
    random.shuffle(todas_las_canciones)
    
    context = {
        'canciones': todas_las_canciones,
        'generos_seleccionados': generos_seleccionados,
        'total_canciones': len(todas_las_canciones),
        'usuario': usuario_actual
    }
    
    return render(request, 'interfaz/lista_reproduccion.html', context)

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
        
         
def perfil_usuario(request):
    # 1. Seguridad: Verificar sesión
    uid = request.session.get('usuario_id')
    if not uid:
        return redirect('login')
    
    usuario = Usuario.objects.get(usuario_id=uid)

    # 2. Obtener redes sociales
    redes = RedesSociales.objects.filter(usuario_id=uid)

    # 3. Lógica del autoplay (buscar la canción elegida)
    cancion_anthem = None
    if usuario.cancion_id:
        try:
            cancion_anthem = Canciones.objects.get(cancion_id=usuario.cancion_id)
        except Canciones.DoesNotExist:
            pass
    
    # 4. Obtener canciones publicadas
    mis_canciones = Canciones.objects.all()[:4]

    context = {
        'usuario' : usuario,
        'redes' : redes, 
        'cancion_anthem' : cancion_anthem,
        'mis_canciones' : mis_canciones,
        'todas_canciones' : Canciones.objects.all()
    }

    return render(request, 'interfaz/perfil.html', context)

def editar_perfil(request):
    # Verificar sesión
    uid = request.session.get('usuario_id')
    if not uid: return redirect('login')

    usuario = Usuario.objects.get(usuario_id=uid)

    if request.method == 'POST':
        print("--- INICIANDO ACTUALIZACIÓN POR SQL ---")
        # Editar Nombre
        nuevo_nombre = request.POST.get('nombre')
        nuevo_apellido = request.POST.get('apellido')
        nueva_bio = request.POST.get('descripcion', '')
        cancion_id = request.POST.get('cancion_anthem_id')

        # Manejo de Foto
        borrar_foto = request.POST.get('eliminar_foto')
        ruta_foto = usuario.foto_perfil_path
        if borrar_foto:
            # Si marcaron borrar, la ruta se vuelve None (o string vacío)
            ruta_foto = None 
            print(">>> Se solicitó eliminar la foto de perfil")
        elif 'foto_perfil' in request.FILES and request.FILES['foto_perfil']:
            # Si NO borraron y SUBIERON una nueva, la guardamos
            imagen = request.FILES['foto_perfil']
            fs = FileSystemStorage()
            filename = fs.save(f"perfiles/user_{uid}_{imagen.name}", imagen)
            ruta_foto = fs.url(filename)

        # Validamos canción (si está vacía, ponemos NULL o 0)
        if not cancion_id:
            cancion_id = None

        # SQL directo
        try:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE usuarios 
                    SET nombre = %s, 
                        apellido = %s, 
                        descripcion = %s, 
                        cancion_id = %s, 
                        foto_perfil_path = %s
                    WHERE usuario_id = %s
                """
                valores = [nuevo_nombre, nuevo_apellido, nueva_bio, cancion_id, ruta_foto, uid]
                cursor.execute(sql, valores)
                print(f"SQL Ejecutado correctamente. Filas afectadas: {cursor.rowcount}")
        except Exception as e:
            print(f"ERROR SQL: {e}")

        nueva_red = request.POST.get('nueva_red_nombre')
        nueva_url = request.POST.get('nueva_red_url')

        if nueva_red and nueva_url:
            RedesSociales.objects.create(
                usuario_id=uid,
                nombre_red=nueva_red,
                url=nueva_url
            )

        return redirect('perfil_usuario')

    return redirect('perfil_usuario')

def eliminar_red_social(request, red_id):
    # 1. Seguridad básica
    uid = request.session.get('usuario_id')
    if not uid: return redirect('login')

    print(f"\n🛑 --- INICIO DIAGNÓSTICO DE BORRADO ---")
    print(f"Intentando borrar ID: {red_id} | Usuario actual: {uid}")

    try:
        with connection.cursor() as cursor:
            # PASO 1: ¿CÓMO SE LLAMAN LAS COLUMNAS?
            # Le preguntamos a la base de datos qué columnas tiene la tabla
            cursor.execute("DESCRIBE redes_sociales")
            columnas = [col[0] for col in cursor.fetchall()]
            print(f"📋 Las columnas en la BD son: {columnas}")

            # PASO 2: INTENTAR BORRAR SEGÚN EL NOMBRE QUE ENCONTREMOS
            filas_borradas = 0
            
            if 'id' in columnas:
                print("👉 Detecté columna 'id'. Usando esa...")
                # Probamos borrando solo por ID primero para ver si es el usuario lo que falla
                cursor.execute("DELETE FROM redes_sociales WHERE id = %s", [red_id])
                filas_borradas = cursor.rowcount
                
            elif 'red_id' in columnas:
                print("👉 Detecté columna 'red_id'. Usando esa...")
                cursor.execute("DELETE FROM redes_sociales WHERE red_id = %s", [red_id])
                filas_borradas = cursor.rowcount
            
            else:
                # Si se llama de otra forma rara (ej: 'red_social_id')
                nombre_id = columnas[0] # Asumimos que la primera es la PK
                print(f"👉 Usando la primera columna encontrada: '{nombre_id}'")
                cursor.execute(f"DELETE FROM redes_sociales WHERE {nombre_id} = %s", [red_id])
                filas_borradas = cursor.rowcount

            if filas_borradas > 0:
                print(f"✅ ¡ÉXITO! Se borraron {filas_borradas} filas.")
            else:
                print("⚠️ FRACASO: La consulta corrió pero no borró nada. El ID no existía.")

    except Exception as e:
        print(f"❌ ERROR EXPLÍCITO: {e}")

    print("🛑 --- FIN DIAGNÓSTICO ---\n")
    return redirect('perfil_usuario')

@csrf_exempt
def calificar_cancion(request):
    """Vista para calificar canciones con estrellas (1-5)"""
    if request.method == 'POST':
        try:
            # Verificar si hay sesión activa
            if 'usuario_id' not in request.session:
                return JsonResponse({
                    'success': False,
                    'message': 'Debes iniciar sesión para calificar canciones'
                })
            
            data = json.loads(request.body)
            cancion_id = data.get('cancion_id')
            rating_value = int(data.get('rating', 0))  # 0 = eliminar rating
            usuario_id = request.session['usuario_id']
            
            print(f"⭐ Usuario {usuario_id} calificando canción {cancion_id} con {rating_value} estrellas")
            
            # Validar valor del rating
            if rating_value < 0 or rating_value > 5:
                return JsonResponse({
                    'success': False,
                    'message': 'El rating debe estar entre 1 y 5'
                })
            
            with connection.cursor() as cursor:
                if rating_value == 0:
                    # Eliminar rating del usuario para esta canción
                    cursor.execute("""
                        DELETE FROM ratings_canciones 
                        WHERE usuario_id = %s AND cancion_id = %s
                    """, [usuario_id, cancion_id])
                    print(f"❌ Rating eliminado para canción {cancion_id}")
                    accion = 'eliminado'
                else:
                    # Verificar si ya existe un rating del usuario
                    cursor.execute("""
                        SELECT rating_id FROM ratings_canciones 
                        WHERE usuario_id = %s AND cancion_id = %s
                    """, [usuario_id, cancion_id])
                    
                    rating_existente = cursor.fetchone()
                    
                    if rating_existente:
                        # Actualizar rating existente
                        cursor.execute("""
                            UPDATE ratings_canciones 
                            SET valor = %s, fecha_rating = NOW()
                            WHERE usuario_id = %s AND cancion_id = %s
                        """, [rating_value, usuario_id, cancion_id])
                        print(f"🔄 Rating actualizado a {rating_value} para canción {cancion_id}")
                        accion = 'actualizado'
                    else:
                        # Insertar nuevo rating
                        cursor.execute("""
                            INSERT INTO ratings_canciones (usuario_id, cancion_id, valor)
                            VALUES (%s, %s, %s)
                        """, [usuario_id, cancion_id, rating_value])
                        print(f"✅ Nuevo rating {rating_value} agregado para canción {cancion_id}")
                        accion = 'agregado'
                
                # Obtener estadísticas actualizadas del rating
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_ratings,
                        AVG(valor) as promedio
                    FROM ratings_canciones
                    WHERE cancion_id = %s
                """, [cancion_id])
                
                estadisticas = cursor.fetchone()
                total_ratings = estadisticas[0] if estadisticas[0] else 0
                promedio = float(estadisticas[1]) if estadisticas[1] else 0.0
                
                # Si se eliminó el rating, obtener el nuevo rating del usuario (será 0)
                user_rating = rating_value if rating_value > 0 else 0
                
                print(f"📊 Estadísticas actualizadas: Promedio={promedio:.1f}, Total={total_ratings}")
                
                return JsonResponse({
                    'success': True,
                    'promedio': round(promedio, 1),
                    'total_ratings': total_ratings,
                    'user_rating': user_rating,
                    'accion': accion,
                    'message': f'Rating {accion} exitosamente'
                })
                
        except Exception as e:
            print(f"❌ Error al calificar canción: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

def obtener_estadisticas_rating(request, cancion_id):
    """Obtener estadísticas detalladas del rating de una canción"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_ratings,
                    AVG(valor) as promedio,
                    MIN(valor) as min_rating,
                    MAX(valor) as max_rating,
                    COUNT(CASE WHEN valor = 5 THEN 1 END) as rating_5,
                    COUNT(CASE WHEN valor = 4 THEN 1 END) as rating_4,
                    COUNT(CASE WHEN valor = 3 THEN 1 END) as rating_3,
                    COUNT(CASE WHEN valor = 2 THEN 1 END) as rating_2,
                    COUNT(CASE WHEN valor = 1 THEN 1 END) as rating_1
                FROM ratings_canciones 
                WHERE cancion_id = %s
            """, [cancion_id])
            
            resultado = cursor.fetchone()
            
            return JsonResponse({
                'success': True,
                'total_ratings': resultado[0] or 0,
                'promedio': float(resultado[1]) if resultado[1] else 0.0,
                'min_rating': resultado[2] or 0,
                'max_rating': resultado[3] or 0,
                'distribucion': {
                    '5_estrellas': resultado[4] or 0,
                    '4_estrellas': resultado[5] or 0,
                    '3_estrellas': resultado[6] or 0,
                    '2_estrellas': resultado[7] or 0,
                    '1_estrella': resultado[8] or 0,
                }
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@csrf_exempt
def buscar_canciones(request):
    """Vista para buscar canciones - BÚSQUEDA GLOBAL"""
    if request.method == 'GET':
        termino = request.GET.get('q', '').strip()
        usuario_id = request.session.get('usuario_id')
        print(f"🔍 Búsqueda: '{termino}'")
        
        if len(termino) < 2:
            return JsonResponse({
                'success': False,
                'message': 'Ingresa al menos 2 caracteres'
            })
        
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT DISTINCT
                        c.cancion_id,
                        c.titulo,
                        c.duracion,
                        c.ruta_archivo,
                        a.titulo as album,
                        a.imagen_portada_path,
                        ar.nombre as artista,
                        g.nombre as genero,
                        COALESCE(likes.total, 0) as likes,
                        COALESCE(dislikes.total, 0) as dislikes,
                        rc.tipo as reaccion_usuario
                    FROM canciones c
                    LEFT JOIN albumes a ON c.album_id = a.album_id
                    LEFT JOIN canciones_artistas ca ON c.cancion_id = ca.cancion_id 
                        AND ca.tipo_participacion = 'Principal'
                    LEFT JOIN artistas ar ON ca.artista_id = ar.artista_id
                    LEFT JOIN canciones_generos cg ON c.cancion_id = cg.cancion_id
                    LEFT JOIN generos g ON cg.genero_id = g.genero_id
                    LEFT JOIN (
                        SELECT cancion_id, COUNT(*) as total 
                        FROM reacciones_canciones 
                        WHERE tipo = 'like' 
                        GROUP BY cancion_id
                    ) likes ON c.cancion_id = likes.cancion_id
                    LEFT JOIN (
                        SELECT cancion_id, COUNT(*) as total 
                        FROM reacciones_canciones 
                        WHERE tipo = 'dislike' 
                        GROUP BY cancion_id
                    ) dislikes ON c.cancion_id = dislikes.cancion_id
                    LEFT JOIN reacciones_canciones rc ON c.cancion_id = rc.cancion_id 
                        AND rc.usuario_id = %s
                    WHERE (
                        c.titulo LIKE %s 
                        OR ar.nombre LIKE %s 
                        OR g.nombre LIKE %s
                        OR a.titulo LIKE %s
                    )
                    ORDER BY c.titulo LIMIT 50
                """
                
                termino_like = f'%{termino}%'
                params = [usuario_id, termino_like, termino_like, termino_like, termino_like]

                cursor.execute(query, params)
                resultados = cursor.fetchall()
                
                print(f"✅ {len(resultados)} canciones encontradas")
                
                canciones = []
                for cancion in resultados:
                    duracion = str(cancion[2]) if cancion[2] else "0:00"
                    if len(duracion) > 5:
                        duracion = duracion[3:8]
                    
                    canciones.append({
                        'id': cancion[0],
                        'titulo': cancion[1],
                        'duracion': duracion,
                        'ruta_archivo': cancion[3],
                        'album': cancion[4] if cancion[4] else 'Sin álbum',
                        'portada': cancion[5] if cancion[5] else 'https://via.placeholder.com/150',
                        'artista': cancion[6] if cancion[6] else 'Artista desconocido',
                        'genero': cancion[7] if cancion[7] else 'Sin género',
                        'likes': int(cancion[8]),
                        'dislikes': int(cancion[9]),
                        'reaccion_usuario': cancion[10]
                    })
                
                return JsonResponse({
                    'success': True,
                    'canciones': canciones,
                    'total': len(canciones)
                })
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

    
@csrf_exempt
def reaccionar_cancion(request):
    """Vista para manejar likes/dislikes de canciones"""
    if request.method == 'POST':
        try:
            # Verificar si hay sesión activa
            if 'usuario_id' not in request.session:
                return JsonResponse({
                    'success': False,
                    'message': 'Debes iniciar sesión para reaccionar'
                })
            
            data = json.loads(request.body)
            cancion_id = data.get('cancion_id')
            tipo_reaccion = data.get('tipo')  # 'like' o 'dislike'
            usuario_id = request.session['usuario_id']
            
            print(f"🎵 Usuario {usuario_id} reaccionando a canción {cancion_id} con {tipo_reaccion}")
            
            if tipo_reaccion not in ['like', 'dislike']:
                return JsonResponse({
                    'success': False,
                    'message': 'Tipo de reacción inválido'
                })
            
            with connection.cursor() as cursor:
                # Verificar si ya existe una reacción
                cursor.execute("""
                    SELECT tipo FROM reacciones_canciones 
                    WHERE usuario_id = %s AND cancion_id = %s
                """, [usuario_id, cancion_id])
                
                reaccion_existente = cursor.fetchone()
                
                if reaccion_existente:
                    tipo_actual = reaccion_existente[0]
                    
                    if tipo_actual == tipo_reaccion:
                        # Si es la misma reacción, ELIMINARLA (toggle off)
                        cursor.execute("""
                            DELETE FROM reacciones_canciones 
                            WHERE usuario_id = %s AND cancion_id = %s
                        """, [usuario_id, cancion_id])
                        print(f"❌ Reacción {tipo_reaccion} eliminada")
                        accion = 'eliminada'
                    else:
                        # Si es diferente, ACTUALIZARLA (cambiar de like a dislike o viceversa)
                        cursor.execute("""
                            UPDATE reacciones_canciones 
                            SET tipo = %s, fecha_reaccion = NOW()
                            WHERE usuario_id = %s AND cancion_id = %s
                        """, [tipo_reaccion, usuario_id, cancion_id])
                        print(f"🔄 Reacción cambiada de {tipo_actual} a {tipo_reaccion}")
                        accion = 'cambiada'
                else:
                    # No existe reacción, CREARLA
                    cursor.execute("""
                        INSERT INTO reacciones_canciones (usuario_id, cancion_id, tipo)
                        VALUES (%s, %s, %s)
                    """, [usuario_id, cancion_id, tipo_reaccion])
                    print(f"✅ Nueva reacción {tipo_reaccion} agregada")
                    accion = 'agregada'
                
                # Obtener contadores actualizados
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN tipo = 'like' THEN 1 ELSE 0 END) as likes,
                        SUM(CASE WHEN tipo = 'dislike' THEN 1 ELSE 0 END) as dislikes
                    FROM reacciones_canciones
                    WHERE cancion_id = %s
                """, [cancion_id])
                
                contadores = cursor.fetchone()
                likes = contadores[0] if contadores[0] else 0
                dislikes = contadores[1] if contadores[1] else 0
                
                # Verificar reacción actual del usuario
                cursor.execute("""
                    SELECT tipo FROM reacciones_canciones 
                    WHERE usuario_id = %s AND cancion_id = %s
                """, [usuario_id, cancion_id])
                
                reaccion_actual = cursor.fetchone()
                reaccion_usuario = reaccion_actual[0] if reaccion_actual else None
                
                print(f"📊 Contadores: {likes} likes, {dislikes} dislikes")
                
                return JsonResponse({
                    'success': True,
                    'accion': accion,
                    'likes': likes,
                    'dislikes': dislikes,
                    'reaccion_usuario': reaccion_usuario,
                    'message': f'Reacción {accion} exitosamente'
                })
                
        except Exception as e:
            print(f"❌ Error al procesar reacción: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })   

@csrf_exempt
def agregar_resena(request):
    """Agregar reseña a una canción. Permite comentario y/o rating.
       Devuelve promedio, total_ratings y user_rating actualizados."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})

    try:
        data = json.loads(request.body)
        cancion_id = data.get('cancion_id')
        comentario = (data.get('comentario') or '').strip()
        rating_raw = data.get('rating', None)
        rating = None
        if rating_raw is not None and rating_raw != '':
            try:
                rating = int(rating_raw)
            except:
                rating = None

        usuario_id = request.session['usuario_id']

        if not cancion_id:
            return JsonResponse({'success': False, 'message': 'Falta cancion_id'})

        created_resena = False
        rating_accion = None

        with connection.cursor() as cursor:
            # Insertar reseña si viene comentario (puntuacion_estrellas nullable)
            if comentario:
                cursor.execute("""
                    INSERT INTO resenas_canciones (usuario_id, cancion_id, comentario, fecha_resena, puntuacion_estrellas)
                    VALUES (%s, %s, %s, NOW(), %s)
                """, [usuario_id, cancion_id, comentario, rating if (rating and rating > 0) else None])
                created_resena = True

            # Si vino rating -> insertar/actualizar ratings_canciones
            if rating is not None:
                if rating < 1 or rating > 5:
                    return JsonResponse({'success': False, 'message': 'Rating debe estar entre 1 y 5'})

                cursor.execute("""
                    SELECT rating_id FROM ratings_canciones WHERE usuario_id = %s AND cancion_id = %s
                """, [usuario_id, cancion_id])
                r = cursor.fetchone()
                if r:
                    cursor.execute("""
                        UPDATE ratings_canciones SET valor = %s, fecha_rating = NOW()
                        WHERE usuario_id = %s AND cancion_id = %s
                    """, [rating, usuario_id, cancion_id])
                    rating_accion = 'actualizado'
                else:
                    cursor.execute("""
                        INSERT INTO ratings_canciones (usuario_id, cancion_id, valor)
                        VALUES (%s, %s, %s)
                    """, [usuario_id, cancion_id, rating])
                    rating_accion = 'agregado'

            # Si no vino comentario ni rating -> error
            if not comentario and rating is None:
                return JsonResponse({'success': False, 'message': 'Envía al menos un comentario o una calificación'})

            # Obtener estadísticas actualizadas del rating
            cursor.execute("""
                SELECT COUNT(*) as total_ratings, AVG(valor) as promedio
                FROM ratings_canciones
                WHERE cancion_id = %s
            """, [cancion_id])
            estad = cursor.fetchone()
            total_ratings = int(estad[0]) if estad and estad[0] else 0
            promedio = float(estad[1]) if estad and estad[1] else 0.0

            # Obtener rating actual del usuario (por si no envió rating ahora)
            cursor.execute("""
                SELECT valor FROM ratings_canciones
                WHERE usuario_id = %s AND cancion_id = %s
            """, [usuario_id, cancion_id])
            ur = cursor.fetchone()
            user_rating = int(ur[0]) if ur and ur[0] else 0

        msgs = []
        if created_resena: msgs.append('Reseña publicada')
        if rating_accion: msgs.append(f'Rating {rating_accion}')
        message = ' y '.join(msgs) if msgs else 'Acción realizada'

        return JsonResponse({
            'success': True,
            'message': message,
            'promedio': round(promedio, 1),
            'total_ratings': total_ratings,
            'user_rating': user_rating
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def obtener_resenas_cancion(request, cancion_id):
    """Obtener reseñas + estadísticas (promedio, total, user_rating) de una canción"""
    usuario_id = request.session.get('usuario_id')
    resenas = []
    
    try:
        with connection.cursor() as cursor:
            # Obtener reseñas - MODIFICADO: usa COALESCE para priorizar rating actual
            cursor.execute("""
                SELECT 
                    r.resena_cancion_id AS resena_id,
                    r.comentario,
                    -- PRIORIDAD: Si hay rating en reseña, usarlo; si no, usar rating general
                    COALESCE(r.puntuacion_estrellas, rc.valor) AS rating,
                    r.fecha_resena,
                    u.nombre,
                    u.foto_perfil_path,
                    u.apellido,

                    -- total likes
                    SUM(CASE WHEN rr.tipo = 'like' THEN 1 ELSE 0 END) AS total_likes,

                    -- total dislikes
                    SUM(CASE WHEN rr.tipo = 'dislike' THEN 1 ELSE 0 END) AS total_dislikes,

                    -- user liked?
                    MAX(CASE WHEN rr.usuario_id = %s AND rr.tipo = 'like' THEN 1 ELSE 0 END) AS user_liked,

                    -- user disliked?
                    MAX(CASE WHEN rr.usuario_id = %s AND rr.tipo = 'dislike' THEN 1 ELSE 0 END) AS user_disliked,

                    r.usuario_id

                FROM resenas_canciones r
                JOIN usuarios u 
                    ON r.usuario_id = u.usuario_id

                LEFT JOIN reacciones_resenas_canciones rr 
                    ON r.resena_cancion_id = rr.resena_cancion_id
                    
                -- NUEVO: LEFT JOIN con ratings_canciones para obtener calificación actual
                LEFT JOIN ratings_canciones rc 
                    ON rc.usuario_id = r.usuario_id AND rc.cancion_id = r.cancion_id

                WHERE r.cancion_id = %s

                GROUP BY 
                    r.resena_cancion_id, 
                    r.comentario,
                    r.puntuacion_estrellas,
                    rc.valor,  -- Agregado al GROUP BY
                    r.fecha_resena,
                    u.nombre,
                    u.apellido,
                    u.foto_perfil_path,
                    r.usuario_id

                ORDER BY r.fecha_resena DESC
            """, [usuario_id, usuario_id, cancion_id])
            
            for row in cursor.fetchall():
                fecha = row[3].strftime('%d/%m/%Y') if row[3] else ''
                resenas.append({
                    'id': row[0],
                    'comentario': row[1],
                    'rating': row[2],  # Ahora es COALESCE(r.puntuacion_estrellas, rc.valor)
                    'fecha': fecha,
                    'nombre': row[4],
                    'foto_perfil': row[5],
                    'apellido': row[6],  # Agregado
                    'likes': row[7],
                    'dislikes': row[8],
                    'user_liked': bool(row[9]),
                    'user_disliked': bool(row[10]),
                    'usuario_id': row[11],
                })
            
            # Resto del código se mantiene igual...
            # Estadísticas globales de ratings
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_ratings,
                    IFNULL(AVG(valor), 0) as promedio
                FROM ratings_canciones
                WHERE cancion_id = %s
            """, [cancion_id])
            estad = cursor.fetchone()
            total_ratings = int(estad[0]) if estad and estad[0] else 0
            promedio = float(estad[1]) if estad and estad[1] else 0.0

            # Rating específico del usuario (si está logueado)
            user_rating = 0
            if usuario_id:
                cursor.execute("""
                    SELECT valor FROM ratings_canciones
                    WHERE cancion_id = %s AND usuario_id = %s
                """, [cancion_id, usuario_id])
                ur = cursor.fetchone()
                if ur and ur[0] is not None:
                    user_rating = int(ur[0])

        return JsonResponse({
            'success': True,
            'resenas': resenas,
            'promedio_rating': round(promedio, 1),
            'total_ratings': total_ratings,
            'user_rating': user_rating
        })
        
    except Exception as e:
        print(f"Error en obtener_resenas_cancion: {e}")
        import traceback; traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def like_resena(request): 
    """Manejar likes/dislikes de reseñas"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        resena_id = data.get('resena_id')
        tipo = data.get('tipo')  # 'like' o 'dislike'
        
        if tipo not in ['like', 'dislike']:
            return JsonResponse({'success': False, 'message': 'Tipo inválido'})
        
        usuario_id = request.session['usuario_id']
        
        with connection.cursor() as cursor:
            # Verificar si ya existe una reacción del usuario a esta reseña
            cursor.execute("""
                SELECT tipo FROM reacciones_resenas_canciones 
                WHERE usuario_id = %s AND resena_cancion_id = %s
            """, [usuario_id, resena_id])
            
            reaccion_existente = cursor.fetchone()
            
            if reaccion_existente:
                tipo_actual = reaccion_existente[0]
                
                if tipo_actual == tipo:
                    # Si es la misma reacción, eliminarla (toggle off)
                    cursor.execute("""
                        DELETE FROM reacciones_resenas_canciones 
                        WHERE usuario_id = %s AND resena_cancion_id = %s
                    """, [usuario_id, resena_id])
                    accion = 'eliminada'
                else:
                    # Si es diferente, actualizarla (cambiar de like a dislike o viceversa)
                    cursor.execute("""
                        UPDATE reacciones_resenas_canciones 
                        SET tipo = %s 
                        WHERE usuario_id = %s AND resena_cancion_id = %s
                    """, [tipo, usuario_id, resena_id])
                    accion = 'cambiada'
            else:
                # Crear nueva reacción
                cursor.execute("""
                    INSERT INTO reacciones_resenas_canciones (usuario_id, resena_cancion_id, tipo)
                    VALUES (%s, %s, %s)
                """, [usuario_id, resena_id, tipo])
                accion = 'agregada'
            
            # Obtener contadores actualizados
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN tipo = 'like' THEN 1 ELSE 0 END) as likes,
                    SUM(CASE WHEN tipo = 'dislike' THEN 1 ELSE 0 END) as dislikes
                FROM reacciones_resenas_canciones
                WHERE resena_cancion_id = %s
            """, [resena_id])
            
            contadores = cursor.fetchone()
            likes = contadores[0] if contadores[0] else 0
            dislikes = contadores[1] if contadores[1] else 0
            
            # Verificar reacción actual del usuario
            cursor.execute("""
                SELECT tipo FROM reacciones_resenas_canciones 
                WHERE usuario_id = %s AND resena_cancion_id = %s
            """, [usuario_id, resena_id])
            
            reaccion_actual = cursor.fetchone()
            reaccion_usuario = reaccion_actual[0] if reaccion_actual else None
            
            return JsonResponse({
                'success': True,
                'accion': accion,
                'likes': likes,
                'dislikes': dislikes,
                'reaccion_usuario': reaccion_usuario,
                'message': f'Reacción {accion} exitosamente'
            })
            
    except Exception as e:
        print(f"Error en like_resena: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})
    
@csrf_exempt
def eliminar_resena(request):
    """Eliminar una reseña (solo el dueño o admin)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    if 'usuario_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Debes iniciar sesión'})
    
    try:
        data = json.loads(request.body)
        resena_id = data.get('resena_id')
        usuario_id = request.session['usuario_id']
        
        if not resena_id:
            return JsonResponse({'success': False, 'message': 'Falta resena_id'})
        
        with connection.cursor() as cursor:
            # Verificar que la reseña exista y que el usuario sea el dueño
            cursor.execute("""
                SELECT usuario_id FROM resenas_canciones 
                WHERE resena_cancion_id = %s
            """, [resena_id])
            
            resena = cursor.fetchone()
            
            if not resena:
                return JsonResponse({'success': False, 'message': 'Reseña no encontrada'})
            
            resena_usuario_id = resena[0]
            
            # Verificar si el usuario es el dueño o es admin
            cursor.execute("""
                SELECT es_admin FROM usuarios WHERE usuario_id = %s
            """, [usuario_id])
            
            usuario = cursor.fetchone()
            es_admin = usuario[0] if usuario else False
            
            if resena_usuario_id != usuario_id and not es_admin:
                return JsonResponse({'success': False, 'message': 'No tienes permiso para eliminar esta reseña'})
            
            # Eliminar reacciones asociadas primero (por integridad referencial)
            cursor.execute("""
                DELETE FROM reacciones_resenas_canciones 
                WHERE resena_cancion_id = %s
            """, [resena_id])
            
            # Eliminar la reseña
            cursor.execute("""
                DELETE FROM resenas_canciones 
                WHERE resena_cancion_id = %s
            """, [resena_id])
            
            # Si esta reseña tenía una calificación en puntuacion_estrellas, eliminarla de ratings_canciones también
            # (opcional, dependiendo de si quieres mantener el rating separado)
            # cursor.execute("""
            #     DELETE FROM ratings_canciones 
            #     WHERE usuario_id = %s AND cancion_id = (
            #         SELECT cancion_id FROM resenas_canciones 
            #         WHERE resena_cancion_id = %s
            #     )
            # """, [usuario_id, resena_id])
            
            return JsonResponse({
                'success': True,
                'message': 'Reseña eliminada exitosamente'
            })
            
    except Exception as e:
        print(f"Error en eliminar_resena: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})
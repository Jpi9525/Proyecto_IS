
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
                    contrasena=password
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
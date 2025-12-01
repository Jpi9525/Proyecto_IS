from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
import json
from .models import Usuario

def index(request):
    return render(request, 'app/LoginScreen.html')

def login(request):
    if request.method == 'POST':
        nombre = request.POST.get('userName')
        contraseña = request.POST.get('passWord')
        
        try:
            # Consulta a la base de datos
            usuario = Usuario.objects.get(userName=nombre)
            if check_password(contraseña, usuario.password):
                # Si existe, guardar en sesión
                request.session['usuario_id'] = usuario.idUser
                request.session['usuario_nombre'] = usuario.userName
                # Redirigir a página de bienvenida
                return redirect('main')
            else: 
                messages.error(request, 'Error: contarseña incorrecta.')
                return redirect('LoginScreen')
            
        except Usuario.DoesNotExist:
            messages.error(request, 'Error: Usuario no encontrado.') 
            return redirect('LoginScreen') # Redirigir a la ruta vacía, que es views.index
    
    # Si es GET, o si fue redirigido después de un POST fallido
    return render(request, 'app/LoginScreen.html')    

def registro(request):
        return render(request, 'app/registro.html')
# NUEVA VISTA PARA GUARDAR EL USUARIO
@csrf_exempt
def guardar_usuario(request):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            data = json.loads(request.body)
            nombre = data.get('name')
            email = data.get('email')
            username = data.get('username')
            password = data.get('password')
            
            # Verificar si el usuario ya existe
            if Usuario.objects.filter(userName=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de usuario ya existe'
                }, status=400)
            
            # Verificar si el email ya existe
            if Usuario.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El email ya está registrado'
                }, status=400)
            
            # Crear el nuevo usuario con contraseña hasheada
            nuevo_usuario = Usuario(
                name=nombre,
                email=email,
                userName=username,
                password=make_password(password)  # Hashear la contraseña
            )
            nuevo_usuario.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Usuario registrado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar usuario: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)

def main(request):
    # Verificar si hay sesión activa
    if 'usuario_id' not in request.session:
        return redirect('index')
    
    contexto = {
        'userName': request.session.get('usuario_nombre')
    }
    return render(request, 'app/main.html', contexto)

def logout(request):
    request.session.flush()  # Eliminar todas las variables de sesión
    return redirect('index')


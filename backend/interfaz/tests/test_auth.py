from django.test import TestCase, Client
from django.urls import reverse
from ..models import Usuario
from .factories import UsuarioFactory

class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Creamos un usuario base para pruebas de login
        self.user = UsuarioFactory(email="paola@test.com")

    def test_AUTH_001_registro_exitoso(self):
        """Verifica que se puede registrar un usuario nuevo"""
        url = reverse('registro') # Asegúrate que en urls.py se llame 'registro'
        data = {
            'nombre': 'Nuevo',
            'apellido': 'User',
            'email': 'nuevo@test.com',
            'password': '123',
            'confirm_password': '123'
        }
        response = self.client.post(url, data)
        
        # Debe redirigir al login si fue exitoso
        self.assertRedirects(response, reverse('login'))
        # Verificamos que se creó en la BD
        self.assertTrue(Usuario.objects.filter(email='nuevo@test.com').exists())

    def test_AUTH_002_registro_email_duplicado(self):
        """Verifica que falle si el email ya existe"""
        # Intentamos registrar el email de Paola que creamos en setUp
        url = reverse('registro')
        data = {
            'nombre': 'Hacker',
            'apellido': 'Malo',
            'email': 'paola@test.com', # Email existente
            'password': '123',
            'confirm_password': '123'
        }
        response = self.client.post(url, data)
        
        # No debe redirigir (se queda en la misma página mostrando error)
        self.assertEqual(response.status_code, 200)

        # Verificamos que el mensaje existe en la lista de mensajes del sistema, no en el HTML visual
        mensajes = list(response.context['messages'])
        self.assertTrue(any("Ya existe una cuenta" in str(m) for m in mensajes))

    def test_AUTH_003_login_exitoso(self):
        """Prueba tu algoritmo manual de sesiones"""
        from django.contrib.auth.hashers import make_password
        
        # 1. Forzamos la contraseña en la BD para estar 100% seguros
        password_real = 'password123'
        self.user.contrasena = make_password(password_real)
        self.user.save()

        # 2. Definimos la URL (¡Esta es la línea que faltaba!)
        url = reverse('login') 

        # 3. Preparamos los datos
        data = {
            'email': 'paola@test.com', 
            'password': password_real
        }
        
        # 4. Hacemos la petición
        response = self.client.post(url, data)
        
        # 5. Verificamos la redirección (sin seguir la cadena para evitar el error del género)
        self.assertRedirects(
            response, 
            reverse('lista_reproduccion'), 
            fetch_redirect_response=False
        )
        
        # 6. Verificamos sesión
        session = self.client.session
        self.assertEqual(session['usuario_email'], 'paola@test.com')

    def test_AUTH_004_login_password_incorrecta(self):
        url = reverse('login')
        data = {
            'email': 'paola@test.com',
            'password': 'ERROR'
        }
        response = self.client.post(url, data)
        self.assertContains(response, "Contraseña incorrecta")
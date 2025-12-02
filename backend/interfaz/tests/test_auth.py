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
        # Busamos el mensaje de error en el HTML
        self.assertContains(response, "Ya existe una cuenta con ese email")

    def test_AUTH_003_login_exitoso(self):
        """Prueba tu algoritmo manual de sesiones"""
        url = reverse('login')
        data = {
            'email': 'paola@test.com',
            'password': 'password123' # La contraseña que pusimos en el Factory
        }
        response = self.client.post(url, data)
        
        # Verificar redirección al home
        self.assertRedirects(response, reverse('home'))
        
        # Verificar que TU variable de sesión se guardó
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
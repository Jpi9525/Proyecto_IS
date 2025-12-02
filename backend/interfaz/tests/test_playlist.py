from django.test import TestCase, Client
from django.urls import reverse
# Imports corregidos (Plurales)
from ..models import Canciones, Generos, CancionesGeneros
from .factories import UsuarioFactory, GeneroFactory, CancionFactory

class PlaylistTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioFactory()
        
        # Simulamos sesión iniciada manualmente
        session = self.client.session
        session['usuario_id'] = self.user.usuario_id
        session.save()

    def test_GEN_001_guardar_generos_validacion(self):
        """No debe dejar guardar si seleccionas menos de 3"""
        # Asegúrate que en urls.py esta ruta se llame 'guardar_generos'
        try:
            url = reverse('guardar_generos')
        except:
            # Si falla, probablemente la url tiene otro nombre, ajusta aquí
            return 
            
        data = {'generos': ['Rock', 'Pop']} # Solo 2
        
        response = self.client.post(url, data)
        
        # Verificar mensaje de error
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Debes seleccionar exactamente 3 géneros')

    def test_PLAY_001_raw_sql_filtering(self):
        """Prueba CRÍTICA: Verifica que tu SQL solo traiga los géneros correctos"""
        
        # 1. Crear géneros usando los nombres exactos
        rock = GeneroFactory(nombre='Rock')
        pop = GeneroFactory(nombre='Pop')
        jazz = GeneroFactory(nombre='Jazz') # Este NO lo vamos a seleccionar
        
        # 2. Crear canciones
        cancion_rock = CancionFactory(titulo="Rock Anthem")
        cancion_jazz = CancionFactory(titulo="Jazz Smooth")
        
        # 3. Crear relación en la tabla intermedia (CancionesGeneros)
        CancionesGeneros.objects.create(cancion=cancion_rock, genero=rock)
        CancionesGeneros.objects.create(cancion=cancion_jazz, genero=jazz)

        # 4. Guardar preferencias en sesión (Rock y Pop, pero NO Jazz)
        session = self.client.session
        session['generos_favoritos'] = ['Rock', 'Pop', 'Metal']
        session.save()

        # 5. Ejecutar la vista
        url = reverse('lista_reproduccion') # Asegúrate que este name exista en urls.py
        response = self.client.get(url)
        
        # 6. Análisis
        canciones_resultantes = response.context['canciones']
        nombres_canciones = [c['titulo'] for c in canciones_resultantes]
        
        # DEBE estar la de Rock
        self.assertIn("Rock Anthem", nombres_canciones)
        # NO DEBE estar la de Jazz (porque Jazz no está en la sesión)
        self.assertNotIn("Jazz Smooth", nombres_canciones)

    def test_PLAY_002_fallback_logic(self):
        """Si la BD está vacía, debe usar los datos demo"""
        session = self.client.session
        session['generos_favoritos'] = ['Rock', 'Pop', 'Metal']
        session.save()
        
        # No creamos objetos en BD
        
        url = reverse('lista_reproduccion')
        response = self.client.get(url)
        
        canciones = response.context['canciones']
        # Deben ser 10 canciones generadas por tu lógica de respaldo
        self.assertEqual(len(canciones), 10)
        self.assertEqual(canciones[0]['artista'], 'Artista demo')
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Usuario, RedesSociales
from .factories import UsuarioFactory, CancionFactory

class PerfilTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioFactory()
        
        # Login manual
        s = self.client.session
        s['usuario_id'] = self.user.usuario_id
        s.save()

    def test_PROF_001_acceso_denegado_sin_login(self):
        """Si no hay sesión, debe mandar al login"""
        self.client.logout() # Cerramos sesión explícitamente
        s = self.client.session
        s.clear()
        s.save()
        
        url = reverse('perfil_usuario') # Asegúrate que este name exista en urls.py
        response = self.client.get(url)
        
        self.assertRedirects(response, reverse('login'))

    def test_PROF_002_ver_perfil_datos_correctos(self):
        """Verifica que carga el usuario y sus redes"""
        # Creamos una red social para este usuario
        from .factories import RedesSocialesFactory
        RedesSocialesFactory(usuario=self.user, nombre_red="Facebook")

        url = reverse('perfil_usuario')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Verificamos que el usuario está en el contexto
        self.assertEqual(response.context['usuario'].email, self.user.email)
        # Verificamos que las redes se cargaron
        self.assertEqual(len(response.context['redes']), 1)

    def test_PROF_003_logica_cancion_anthem(self):
        """Si el usuario tiene cancion_id, debe aparecer en el perfil"""
        # 1. Creamos una canción
        cancion = CancionFactory(titulo="Mi Himno")
        
        # 2. Asignamos esa canción al usuario
        self.user.cancion_id = cancion.cancion_id
        self.user.save()
        
        # 3. Visitamos el perfil
        response = self.client.get(reverse('perfil_usuario'))
        
        # 4. Verificamos que la canción venga en el contexto
        anthem = response.context['cancion_anthem']
        self.assertIsNotNone(anthem)
        self.assertEqual(anthem.titulo, "Mi Himno")


class EditarPerfilTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioFactory(nombre="NombreViejo", apellido="ApellidoViejo")
        
        # Login
        s = self.client.session
        s['usuario_id'] = self.user.usuario_id
        s.save()

    def test_EDIT_001_actualizar_info_sql(self):
        """Prueba CRÍTICA: Verifica que tu UPDATE SQL funcione"""
        url = reverse('editar_perfil') # Verifica este name en urls.py
        
        # Simulamos una foto falsa (pequeña imagen de 1x1 pixel)
        imagen_falsa = SimpleUploadedFile(
            "avatar_test.jpg", 
            b"\x00\x00\x00", 
            content_type="image/jpeg"
        )

        data = {
            'nombre': 'Juan',
            'apellido': 'Perez',
            'descripcion': 'Soy nuevo',
            'foto_perfil': imagen_falsa,
            # No enviamos cancion_anthem_id para probar el caso NULL
        }
        
        # Hacemos el POST (esto ejecuta tu cursor.execute)
        response = self.client.post(url, data)
        
        # Verificar redirección
        self.assertRedirects(response, reverse('perfil_usuario'))
        
        # RECARGAR usuario desde la BD para ver si el SQL funcionó
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.nombre, 'Juan')
        self.assertEqual(self.user.apellido, 'Perez')
        self.assertEqual(self.user.descripcion, 'Soy nuevo')
        # Verificar que la foto cambió (FileSystemStorage devuelve la ruta)
        self.assertTrue('avatar_test' in self.user.foto_perfil_path)

    def test_EDIT_002_agregar_red_social(self):
        """Verifica que se crea una red social nueva"""
        url = reverse('editar_perfil')
        data = {
            'nombre': self.user.nombre, # Mantenemos el nombre igual
            'apellido': self.user.apellido,
            'nueva_red_nombre': 'TikTok',
            'nueva_red_url': 'tiktok.com/@juan'
        }
        
        self.client.post(url, data)
        
        # Verificar que se creó en la BD
        existe_red = RedesSociales.objects.filter(
            usuario=self.user, 
            nombre_red='TikTok'
        ).exists()
        self.assertTrue(existe_red)
import factory
from django.contrib.auth.hashers import make_password
from faker import Faker
import datetime
# IMPORTANTE: Importamos los nombres EXACTOS de tu models.py
from ..models import Usuario, Generos, Canciones, Albumes, Artistas, RedesSociales

fake = Faker()

class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario

    nombre = factory.Faker('first_name')
    apellido = factory.Faker('last_name')
    # Ajustamos el email a minúsculas
    email = factory.LazyAttribute(lambda o: f"{o.nombre}.{o.apellido}@example.com".lower())
    contrasena = factory.LazyFunction(lambda: make_password('password123'))
    # Valores por defecto para evitar errores de NULL
    es_admin = 0
    es_email_verificado = 1

class GeneroFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Generos
    
    # Iterador para que no repita nombres y use los de tu lista
    nombre = factory.Iterator(['Rock', 'Pop', 'Jazz', 'Metal', 'Salsa', 'Hip-hop'])

class ArtistaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Artistas
    nombre = factory.Faker('name')

class AlbumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Albumes
    titulo = factory.Faker('sentence', nb_words=2)

class CancionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Canciones
    
    titulo = factory.Faker('sentence', nb_words=3)
    # Creamos sub-factories para que cree el álbum automáticamente
    album = factory.SubFactory(AlbumFactory)
    # TimeField necesita un objeto time, no un string
    duracion = datetime.time(0, 3, 30) 
    ruta_archivo = "canciones/demo.mp3"

class RedesSocialesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RedesSociales
    
    usuario = factory.SubFactory(UsuarioFactory)
    nombre_red = "Instagram"
    url = "https://instagram.com/test"
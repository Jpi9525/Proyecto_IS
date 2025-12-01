from django.db import models
from django.contrib.auth.hashers import make_password #para realizar hasheo de contraseña

class Usuario(models.Model):
    userName = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=50, default='')
    email = models.EmailField(max_length=100, unique=True)
    idUser = models.AutoField(primary_key=True)
    class Meta:
        db_table = 'userlogin'

        def __str__(self):
            return self.userName

# backend/interfaz/tests/runner.py
from django.test.runner import DiscoverRunner
from django.apps import apps

class ForceManagedModelTestRunner(DiscoverRunner):
    """
    Este corredor fuerza a que todos los modelos sean managed=True
    SOLO durante las pruebas. Así Django crea las tablas completas
    en la base de datos de prueba temporal.
    """
    def setup_test_environment(self, *args, **kwargs):
        # Buscamos todos los modelos de tu proyecto
        for model in apps.get_models():
            # Los obligamos a ser gestionados por Django
            model._meta.managed = True
        
        super().setup_test_environment(*args, **kwargs)
# backend/interfaz/tests/runner.py
from django.test.runner import DiscoverRunner
from django.apps import apps
from django.conf import settings # <--- Nuevo import importante

class ForceManagedModelTestRunner(DiscoverRunner):
    """
    Corredor de pruebas para Bases de Datos Legacy.
    1. Fuerza managed = True
    2. DESACTIVA las migraciones para leer directo del models.py
    """
    def setup_test_environment(self, *args, **kwargs):
        # 1. Forzamos a que los modelos sean gestionados
        for model in apps.get_models():
            model._meta.managed = True
        
        # 2. LA SOLUCIÓN DEFINITIVA:
        # Le decimos a Django que la app 'interfaz' NO tiene migraciones.
        # Esto obliga a Django a crear la BD basándose solo en el código de models.py
        # Asegúrate de cambiar 'interfaz' si tu app tiene otro nombre en settings
        settings.MIGRATION_MODULES = {'interfaz': None}
        
        super().setup_test_environment(*args, **kwargs)
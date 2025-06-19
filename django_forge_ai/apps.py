from django.apps import AppConfig


class DjangoForgeAIConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_forge_ai"
    verbose_name = "Django Forge AI"

    def ready(self):
        """Import signal handlers and other initialization code"""
        try:
            import django_forge_ai.signals  # noqa
        except ImportError:
            pass


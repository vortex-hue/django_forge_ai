from django.apps import AppConfig


class AgentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_forge_ai.agents"
    verbose_name = "Django Forge AI Agents"
    
    def ready(self):
        """Import admin when app is ready"""
        try:
            import django_forge_ai.agents.admin  # noqa
        except ImportError:
            pass


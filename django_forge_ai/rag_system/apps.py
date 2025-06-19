from django.apps import AppConfig


class RAGSystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_forge_ai.rag_system"
    verbose_name = "Django Forge AI RAG System"
    
    def ready(self):
        """Import admin when app is ready"""
        try:
            import django_forge_ai.rag_system.admin  # noqa
        except ImportError:
            pass


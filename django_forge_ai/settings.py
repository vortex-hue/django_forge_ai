"""
Default settings structure for DjangoForgeAI.
These can be overridden in your Django project's settings.py
"""
from django.conf import settings

# LLM Configuration
DJANGO_FORGE_AI_LLM_PROVIDER = getattr(settings, "DJANGO_FORGE_AI_LLM_PROVIDER", "openai")
DJANGO_FORGE_AI_OPENAI_API_KEY = getattr(settings, "DJANGO_FORGE_AI_OPENAI_API_KEY", None)
DJANGO_FORGE_AI_ANTHROPIC_API_KEY = getattr(settings, "DJANGO_FORGE_AI_ANTHROPIC_API_KEY", None)
DJANGO_FORGE_AI_OPENAI_MODEL = getattr(settings, "DJANGO_FORGE_AI_OPENAI_MODEL", "gpt-3.5-turbo")
DJANGO_FORGE_AI_ANTHROPIC_MODEL = getattr(settings, "DJANGO_FORGE_AI_ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
DJANGO_FORGE_AI_EMBEDDING_MODEL = getattr(settings, "DJANGO_FORGE_AI_EMBEDDING_MODEL", "text-embedding-3-small")
DJANGO_FORGE_AI_MAX_TOKENS = getattr(settings, "DJANGO_FORGE_AI_MAX_TOKENS", 1000)

# Content Moderation
DJANGO_FORGE_AI_MODERATION_KEYWORDS = getattr(
    settings,
    "DJANGO_FORGE_AI_MODERATION_KEYWORDS",
    []
)

# Vector Database Configuration
DJANGO_FORGE_AI_VECTOR_DB = getattr(settings, "DJANGO_FORGE_AI_VECTOR_DB", "chroma")
DJANGO_FORGE_AI_VECTOR_DB_PATH = getattr(settings, "DJANGO_FORGE_AI_VECTOR_DB_PATH", "./vector_db")

# ChromaDB Configuration
DJANGO_FORGE_AI_CHROMA_HOST = getattr(settings, "DJANGO_FORGE_AI_CHROMA_HOST", "localhost")
DJANGO_FORGE_AI_CHROMA_PORT = getattr(settings, "DJANGO_FORGE_AI_CHROMA_PORT", 8000)

# Qdrant Configuration
DJANGO_FORGE_AI_QDRANT_HOST = getattr(settings, "DJANGO_FORGE_AI_QDRANT_HOST", "localhost")
DJANGO_FORGE_AI_QDRANT_PORT = getattr(settings, "DJANGO_FORGE_AI_QDRANT_PORT", 6333)
DJANGO_FORGE_AI_QDRANT_COLLECTION = getattr(settings, "DJANGO_FORGE_AI_QDRANT_COLLECTION", "django_forge_ai")

# PGVector Configuration (requires django.contrib.postgres)
DJANGO_FORGE_AI_PGVECTOR_DB_NAME = getattr(settings, "DJANGO_FORGE_AI_PGVECTOR_DB_NAME", "default")

# Celery Configuration
DJANGO_FORGE_AI_USE_CELERY = getattr(settings, "DJANGO_FORGE_AI_USE_CELERY", True)
DJANGO_FORGE_AI_CELERY_TASK_ROUTE = getattr(
    settings,
    "DJANGO_FORGE_AI_CELERY_TASK_ROUTE",
    "django_forge_ai.tasks"
)

# RAG Configuration
DJANGO_FORGE_AI_RAG_CHUNK_SIZE = getattr(settings, "DJANGO_FORGE_AI_RAG_CHUNK_SIZE", 1000)
DJANGO_FORGE_AI_RAG_CHUNK_OVERLAP = getattr(settings, "DJANGO_FORGE_AI_RAG_CHUNK_OVERLAP", 200)
DJANGO_FORGE_AI_RAG_TOP_K = getattr(settings, "DJANGO_FORGE_AI_RAG_TOP_K", 5)

# Agent Configuration
DJANGO_FORGE_AI_AGENT_MAX_ITERATIONS = getattr(settings, "DJANGO_FORGE_AI_AGENT_MAX_ITERATIONS", 10)
DJANGO_FORGE_AI_AGENT_TIMEOUT = getattr(settings, "DJANGO_FORGE_AI_AGENT_TIMEOUT", 300)
# Fix
# Update
# Update
# Update
# Update
# Refactor
# Fix
# Fix
# Improve
# Fix
# Update
# Fix
# Fix
# Improve
# Update
# Update
# Fix
# Update


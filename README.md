# DjangoForgeAI

A comprehensive, plug-and-play toolkit that seamlessly integrates modern AI/LLM functionalities directly into your Django projects. DjangoForgeAI provides "batteries-included" solutions for common AI engineering tasks, including AI-powered admin fields, native RAG system integration, and configurable AI agents, all manageable through the Django admin interface.

## Features

### 1. AI-Powered Admin & Model Fields

- **AICharField / AITextField**: Custom model fields that can automatically generate summaries or content from other fields in the model using an LLM.
- **AIAdminMixin**: A mixin for ModelAdmin classes that adds a "Generate with AI" button next to specified text fields.
- **AIModeratedField**: A field that automatically runs AI-powered content moderation upon save.

### 2. Native RAG System Integration

- **Knowledge Base Management**: Upload documents, define data sources (e.g., website URLs), and manage vector stores through the Django admin.
- **Vector DB Connectors**: Pluggable backends for popular vector databases (ChromaDB, Qdrant, PGVector).
- **SemanticSearchMixin**: A mixin for QuerySets that enables semantic search against your RAG knowledge base.

### 3. Configurable AI Agents & Automation

- **Agent Management Dashboard**: Define agents (persona, tools, goals) and assign them to specific tasks through the admin.
- **AgentTaskQueue**: Integration with Celery to execute agent tasks in the background and log their progress.

## Installation

```bash
pip install django-forge-ai
```

Or install from source:

```bash
git clone https://github.com/yourusername/django-forge-ai.git
cd django-forge-ai
pip install -e .
```

## Quick Start

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'django_forge_ai',
    'django_forge_ai.rag_system',
    'django_forge_ai.agents',
]
```

### 2. Configure Settings

```python
# settings.py

# LLM Configuration
DJANGO_FORGE_AI_LLM_PROVIDER = "openai"  # or "anthropic"
DJANGO_FORGE_AI_OPENAI_API_KEY = "your-openai-api-key"
# or
DJANGO_FORGE_AI_ANTHROPIC_API_KEY = "your-anthropic-api-key"

# Vector Database Configuration
DJANGO_FORGE_AI_VECTOR_DB = "chroma"  # or "qdrant", "pgvector"
DJANGO_FORGE_AI_VECTOR_DB_PATH = "./vector_db"

# Celery Configuration (optional, for async tasks)
DJANGO_FORGE_AI_USE_CELERY = True
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Use AI-Powered Fields

```python
# models.py
from django.db import models
from django_forge_ai.models import AICharField, AITextField, AIModeratedField

class Article(models.Model):
    title = models.CharField(max_length=200)
    
    # Auto-generate summary from title
    summary = AICharField(
        max_length=200,
        ai_generate_from=['title'],
        ai_prompt_template="Generate a summary of: {title}",
        ai_auto_generate=True
    )
    
    # Generate content with AI
    content = AITextField(
        ai_generate_from=['title'],
        ai_prompt_template="Write an article about: {title}"
    )
    
    # Moderated content
    user_comment = AIModeratedField(
        moderation_strict=True,
        raise_on_violation=True
    )
```

### 5. Use AIAdminMixin

```python
# admin.py
from django.contrib import admin
from django_forge_ai.admin_integration.mixins import AIAdminMixin
from .models import Article

@admin.register(Article)
class ArticleAdmin(AIAdminMixin, admin.ModelAdmin):
    ai_fields = ['summary', 'content']
    ai_prompts = {
        'summary': 'Generate a summary of: {title}',
        'content': 'Write an article about: {title}'
    }
    ai_context_fields = {
        'summary': ['title'],
        'content': ['title']
    }
```

### 6. Set Up RAG System

1. Create a Knowledge Base in the Django admin
2. Upload documents or add URLs
3. Generate embeddings (admin action)
4. Use semantic search:

```python
from django_forge_ai.rag_system.mixins import SemanticSearchMixin
from django.db import models

class ArticleQuerySet(SemanticSearchMixin, models.QuerySet):
    pass

class Article(models.Model):
    objects = ArticleQuerySet.as_manager()
    
# Usage
results = Article.objects.semantic_search("What is Django?")
```

### 7. Create AI Agents

1. Create an Agent Configuration in the Django admin
2. Define persona, goals, and tools
3. Create tasks and execute them (async with Celery)

## Configuration

### LLM Providers

DjangoForgeAI supports multiple LLM providers:

- **OpenAI**: Set `DJANGO_FORGE_AI_LLM_PROVIDER = "openai"` and provide `DJANGO_FORGE_AI_OPENAI_API_KEY`
- **Anthropic**: Set `DJANGO_FORGE_AI_LLM_PROVIDER = "anthropic"` and provide `DJANGO_FORGE_AI_ANTHROPIC_API_KEY`

### Vector Databases

- **ChromaDB**: Default, file-based storage
- **Qdrant**: Requires Qdrant server running
- **PGVector**: Requires PostgreSQL with pgvector extension

### Celery Integration

For async task execution, configure Celery:

```python
# celery.py
from celery import Celery

app = Celery('your_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

## Requirements

- Python >= 3.8
- Django >= 3.2
- OpenAI API key or Anthropic API key
- (Optional) Celery for async tasks
- (Optional) Vector database (ChromaDB, Qdrant, or PostgreSQL with pgvector)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.

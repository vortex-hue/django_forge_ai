"""
Admin mixins for adding AI functionality to Django admin.
"""
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json

from ..utils.llm_client import get_llm_client
from ..utils.validation import ContentGenerationRequest, ContentGenerationResponse


class AIAdminMixin:
    """
    Mixin for ModelAdmin classes that adds "Generate with AI" functionality.
    
    Usage:
        class ArticleAdmin(AIAdminMixin, admin.ModelAdmin):
            ai_fields = ['summary', 'content']
            ai_prompts = {
                'summary': 'Generate a summary of: {title}',
                'content': 'Write an article about: {title}'
            }
    """
    
    ai_fields = []  # List of field names that support AI generation
    ai_prompts = {}  # Dict mapping field names to prompt templates
    ai_context_fields = {}  # Dict mapping field names to context field lists
    
    def get_urls(self):
        """Add custom URLs for AI generation"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/generate-ai/',
                self.admin_site.admin_view(self.generate_ai_view),
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_generate_ai',
            ),
        ]
        return custom_urls + urls
    
    def get_form(self, request, obj=None, **kwargs):
        """Override form to add AI generation buttons"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add AI generation JavaScript and buttons
        if hasattr(form, 'Meta') and hasattr(form.Meta, 'widgets'):
            # This will be handled in the template
            pass
        
        return form
    
    @method_decorator(csrf_exempt)
    @method_decorator(require_http_methods(["POST"]))
    def generate_ai_view(self, request, object_id):
        """
        AJAX endpoint for generating AI content.
        Expects JSON: {'field': 'field_name', 'context': {...}}
        """
        try:
            obj = self.get_object(request, object_id)
            if obj is None:
                return JsonResponse({'error': 'Object not found'}, status=404)
            
            data = json.loads(request.body)
            field_name = data.get('field')
            context = data.get('context', {})
            
            if field_name not in self.ai_fields:
                return JsonResponse(
                    {'error': f'Field {field_name} does not support AI generation'},
                    status=400
                )
            
            # Get prompt template
            prompt_template = self.ai_prompts.get(field_name, '')
            if not prompt_template:
                return JsonResponse(
                    {'error': f'No prompt template defined for field {field_name}'},
                    status=400
                )
            
            # Build context from object fields
            full_context = {}
            context_fields = self.ai_context_fields.get(field_name, [])
            for ctx_field in context_fields:
                if hasattr(obj, ctx_field):
                    full_context[ctx_field] = str(getattr(obj, ctx_field, ''))
            
            # Merge with provided context
            full_context.update(context)
            
            # Format prompt
            try:
                prompt = prompt_template.format(**full_context)
            except KeyError as e:
                return JsonResponse(
                    {'error': f'Missing context field: {e}'},
                    status=400
                )
            
            # Generate content
            llm_client = get_llm_client()
            generated_content = llm_client.generate(prompt=prompt)
            
            return JsonResponse({
                'success': True,
                'content': generated_content,
                'field': field_name
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    class Media:
        """Add custom JavaScript and CSS for AI buttons"""
        js = ('admin/js/ai_generation.js',)
        css = {
            'all': ('admin/css/ai_generation.css',)
        }


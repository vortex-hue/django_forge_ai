"""
Additional admin views for AI functionality.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json

from ..utils.llm_client import get_llm_client


@method_decorator(csrf_exempt, name='dispatch')
class AIGenerationView:
    """Base view for AI generation endpoints"""
    
    @staticmethod
    def generate(request):
        """Handle AI generation request"""
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt')
            context = data.get('context', {})
            
            if not prompt:
                return JsonResponse({'error': 'Prompt is required'}, status=400)
            
            # Build full prompt with context
            if context:
                prompt = prompt.format(**context)
            
            llm_client = get_llm_client()
            generated = llm_client.generate(prompt=prompt)
            
            return JsonResponse({
                'success': True,
                'content': generated
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


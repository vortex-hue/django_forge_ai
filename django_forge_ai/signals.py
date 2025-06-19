"""
Signal handlers for DjangoForgeAI.
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import AICharField, AITextField, AIModeratedField


# Signals are optional and can be used for additional functionality
# For now, we'll keep this file minimal as the main logic is in the field classes


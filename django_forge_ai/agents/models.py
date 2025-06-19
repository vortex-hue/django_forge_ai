"""
Models for AI agent management and task execution.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import json


class AgentConfig(models.Model):
    """
    Configuration for an AI agent.
    """
    name = models.CharField(max_length=200, unique=True)
    persona = models.TextField(help_text="Description of the agent's persona and capabilities")
    goals = models.JSONField(
        default=list,
        help_text="List of goals the agent should accomplish"
    )
    tools = models.JSONField(
        default=list,
        help_text="List of available tools (e.g., ['web_search', 'database_query'])"
    )
    system_prompt = models.TextField(
        blank=True,
        help_text="Custom system prompt (optional, will use default if empty)"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Sampling temperature (0.0 to 2.0)"
    )
    max_iterations = models.IntegerField(
        default=10,
        help_text="Maximum number of iterations the agent can perform"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'agents'
        verbose_name = "Agent Configuration"
        verbose_name_plural = "Agent Configurations"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate agent configuration"""
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValidationError(_("Temperature must be between 0.0 and 2.0"))
        if self.max_iterations < 1:
            raise ValidationError(_("Max iterations must be at least 1"))


class AgentTask(models.Model):
    """
    Represents a task assigned to an agent.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    agent = models.ForeignKey(
        AgentConfig,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    task_description = models.TextField(help_text="Description of the task to execute")
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context for the task"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    result = models.TextField(blank=True, help_text="Result of the task execution")
    error = models.TextField(blank=True, help_text="Error message if task failed")
    iterations_used = models.IntegerField(default=0, help_text="Number of iterations used")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'agents'
        verbose_name = "Agent Task"
        verbose_name_plural = "Agent Tasks"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.agent.name} - {self.task_description[:50]}"
    
    def mark_running(self):
        """Mark task as running"""
        from django.utils import timezone
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, result: str):
        """Mark task as completed with result"""
        from django.utils import timezone
        self.status = 'completed'
        self.result = result
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'result', 'completed_at'])
    
    def mark_failed(self, error: str):
        """Mark task as failed with error"""
        from django.utils import timezone
        self.status = 'failed'
        self.error = error
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'error', 'completed_at'])


class AgentTaskLog(models.Model):
    """
    Log entries for agent task execution.
    """
    task = models.ForeignKey(
        AgentTask,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    iteration = models.IntegerField(help_text="Iteration number")
    action = models.CharField(max_length=200, help_text="Action taken by agent")
    observation = models.TextField(help_text="Observation or result of action")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'agents'
        verbose_name = "Agent Task Log"
        verbose_name_plural = "Agent Task Logs"
        ordering = ['task', 'iteration', 'created_at']
        indexes = [
            models.Index(fields=['task', 'iteration']),
        ]
    
    def __str__(self):
        return f"{self.task} - Iteration {self.iteration}: {self.action}"


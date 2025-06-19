"""
Admin interface for agent management.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import AgentConfig, AgentTask, AgentTaskLog
from ..tasks import execute_agent_task_async


@admin.register(AgentConfig)
class AgentConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'task_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'persona']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'persona', 'is_active')
        }),
        ('Agent Configuration', {
            'fields': (
                'goals',
                'tools',
                'system_prompt',
                'temperature',
                'max_iterations'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def task_count(self, obj):
        """Display number of tasks"""
        count = obj.tasks.count()
        app_label = obj._meta.app_label
        model_name = 'agenttask'
        url = reverse(f'admin:{app_label}_{model_name}_changelist')
        return format_html(
            '<a href="{}?agent__id__exact={}">{} tasks</a>',
            url,
            obj.id,
            count
        )
    task_count.short_description = 'Tasks'


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'agent',
        'task_preview',
        'status',
        'iterations_used',
        'created_at',
        'completed_at'
    ]
    list_filter = ['agent', 'status', 'created_at']
    search_fields = ['task_description', 'result', 'error']
    readonly_fields = [
        'created_at',
        'updated_at',
        'started_at',
        'completed_at',
        'logs_preview'
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('agent', 'task_description', 'context')
        }),
        ('Execution Status', {
            'fields': (
                'status',
                'iterations_used',
                'result',
                'error',
                'logs_preview'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['execute_tasks']
    
    def task_preview(self, obj):
        """Preview of task description"""
        preview = obj.task_description[:100]
        if len(obj.task_description) > 100:
            preview += "..."
        return preview
    task_preview.short_description = 'Task'
    
    def logs_preview(self, obj):
        """Preview of task logs"""
        logs = obj.logs.all()[:10]
        if not logs.exists():
            return "No logs yet"
        
        log_list = []
        for log in logs:
            log_list.append(
                f"<li>Iteration {log.iteration}: {log.action} - {log.observation[:100]}...</li>"
            )
        
        return format_html('<ul>{}</ul>', ''.join(log_list))
    logs_preview.short_description = 'Recent Logs'
    
    def execute_tasks(self, request, queryset):
        """Admin action to execute selected tasks"""
        count = 0
        for task in queryset:
            if task.status == 'pending':
                # Trigger async task execution
                execute_agent_task_async.delay(task.id)
                count += 1
        
        self.message_user(
            request,
            f"Initiated execution for {count} task(s)."
        )
    execute_tasks.short_description = "Execute selected tasks"


@admin.register(AgentTaskLog)
class AgentTaskLogAdmin(admin.ModelAdmin):
    list_display = ['task', 'iteration', 'action', 'observation_preview', 'created_at']
    list_filter = ['task__agent', 'iteration', 'created_at']
    search_fields = ['action', 'observation']
    readonly_fields = ['created_at']
    
    def observation_preview(self, obj):
        """Preview of observation"""
        preview = obj.observation[:200]
        if len(obj.observation) > 200:
            preview += "..."
        return preview
    observation_preview.short_description = 'Observation'


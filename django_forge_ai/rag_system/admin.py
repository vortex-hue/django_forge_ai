"""
Admin interface for RAG system models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import KnowledgeBase, Document, DocumentChunk
from ..tasks import generate_embeddings_task


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'vector_db_type', 'is_active', 'document_count', 'created_at']
    list_filter = ['is_active', 'vector_db_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Vector Database Configuration', {
            'fields': ('vector_db_type', 'collection_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_count(self, obj):
        """Display number of documents"""
        count = obj.documents.count()
        app_label = obj._meta.app_label
        model_name = 'document'
        url = reverse(f'admin:{app_label}_{model_name}_changelist')
        return format_html(
            '<a href="{}?knowledge_base__id__exact={}">{} documents</a>',
            url,
            obj.id,
            count
        )
    document_count.short_description = 'Documents'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'knowledge_base',
        'source_type',
        'embedding_status',
        'chunk_count',
        'created_at'
    ]
    list_filter = [
        'knowledge_base',
        'source_type',
        'embedding_status',
        'is_embedded',
        'created_at'
    ]
    search_fields = ['title', 'content']
    readonly_fields = [
        'created_at',
        'updated_at',
        'embedding_status',
        'chunk_count',
        'chunks_preview'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('knowledge_base', 'title', 'content')
        }),
        ('Source Information', {
            'fields': ('source_type', 'source_url', 'file_path')
        }),
        ('Embedding Status', {
            'fields': ('is_embedded', 'embedding_status', 'chunk_count', 'chunks_preview')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['generate_embeddings']
    
    def chunks_preview(self, obj):
        """Preview of document chunks"""
        chunks = obj.chunks.all()[:5]
        if not chunks.exists():
            return "No chunks yet"
        
        chunk_list = []
        for chunk in chunks:
            chunk_list.append(
                f"<li>Chunk {chunk.chunk_index}: {chunk.content[:100]}...</li>"
            )
        
        return format_html(
            '<ul>{}</ul>',
            ''.join(chunk_list)
        )
    chunks_preview.short_description = 'Chunks Preview'
    
    def generate_embeddings(self, request, queryset):
        """Admin action to generate embeddings for selected documents"""
        count = 0
        for document in queryset:
            if document.embedding_status != 'processing':
                document.embedding_status = 'pending'
                document.save()
                # Trigger async task
                generate_embeddings_task.delay(document.id)
                count += 1
        
        self.message_user(
            request,
            f"Initiated embedding generation for {count} document(s)."
        )
    generate_embeddings.short_description = "Generate embeddings for selected documents"


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'content_preview', 'has_embedding', 'created_at']
    list_filter = ['document__knowledge_base', 'created_at']
    search_fields = ['content', 'document__title']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        """Preview of chunk content"""
        preview = obj.content[:200]
        if len(obj.content) > 200:
            preview += "..."
        return preview
    content_preview.short_description = 'Content'
    
    def has_embedding(self, obj):
        """Check if chunk has embedding"""
        return bool(obj.embedding and len(obj.embedding) > 0)
    has_embedding.boolean = True
    has_embedding.short_description = 'Has Embedding'


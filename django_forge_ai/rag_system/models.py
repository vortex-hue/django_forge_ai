"""
Models for RAG system: KnowledgeBase, Document, and related entities.
"""
from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os


class KnowledgeBase(models.Model):
    """
    Represents a knowledge base for RAG operations.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, help_text="Only active knowledge bases are used for search")
    vector_db_type = models.CharField(
        max_length=50,
        choices=[
            ('chroma', 'ChromaDB'),
            ('qdrant', 'Qdrant'),
            ('pgvector', 'PGVector'),
        ],
        default='chroma'
    )
    collection_name = models.CharField(max_length=200, default='default')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'rag_system'
        verbose_name = "Knowledge Base"
        verbose_name_plural = "Knowledge Bases"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate knowledge base configuration"""
        if self.is_active:
            # Check if there's already an active knowledge base of the same type
            existing = KnowledgeBase.objects.filter(
                is_active=True,
                vector_db_type=self.vector_db_type
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    _("There is already an active knowledge base for this vector DB type.")
                )


class Document(models.Model):
    """
    Represents a document in a knowledge base.
    """
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    title = models.CharField(max_length=500)
    content = models.TextField()
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('upload', 'File Upload'),
            ('url', 'URL'),
            ('text', 'Manual Text'),
        ],
        default='text'
    )
    source_url = models.URLField(blank=True, null=True, validators=[URLValidator()])
    file_path = models.CharField(max_length=1000, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_embedded = models.BooleanField(default=False, help_text="Whether embeddings have been generated")
    embedding_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    chunk_count = models.IntegerField(default=0, help_text="Number of chunks created from this document")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'rag_system'
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['knowledge_base', 'is_embedded']),
            models.Index(fields=['embedding_status']),
        ]
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """Validate document"""
        if self.source_type == 'url' and not self.source_url:
            raise ValidationError(_("source_url is required when source_type is 'url'"))
        if self.source_type == 'upload' and not self.file_path:
            raise ValidationError(_("file_path is required when source_type is 'upload'"))


class DocumentChunk(models.Model):
    """
    Represents a chunk of a document for embedding.
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_index = models.IntegerField(help_text="Index of this chunk in the document")
    content = models.TextField()
    start_char = models.IntegerField(help_text="Starting character position in original document")
    end_char = models.IntegerField(help_text="Ending character position in original document")
    embedding = models.JSONField(default=list, blank=True, help_text="Embedding vector")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'rag_system'
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"
        ordering = ['document', 'chunk_index']
        unique_together = [['document', 'chunk_index']]
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
        ]
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"


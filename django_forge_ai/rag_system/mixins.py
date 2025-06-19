"""
QuerySet mixins for semantic search functionality.
"""
from django.db import models
from typing import List, Dict, Any
from .vector_utils import get_vector_db_connector
from ..utils.llm_client import get_llm_client


class SemanticSearchMixin:
    """
    Mixin for QuerySets that enables semantic search against RAG knowledge base.
    
    Usage:
        class ArticleQuerySet(SemanticSearchMixin, models.QuerySet):
            pass
        
        class Article(models.Model):
            objects = ArticleQuerySet.as_manager()
    """
    
    def semantic_search(
        self,
        query: str,
        knowledge_base_name: str = None,
        top_k: int = 5,
        filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using RAG system.
        
        Args:
            query: Search query text
            knowledge_base_name: Name of knowledge base to search (optional)
            top_k: Number of results to return
            filter: Metadata filters
        
        Returns:
            List of search results with metadata
        """
        from .models import KnowledgeBase
        
        # Get active knowledge base
        if knowledge_base_name:
            kb = KnowledgeBase.objects.get(name=knowledge_base_name, is_active=True)
        else:
            kb = KnowledgeBase.objects.filter(is_active=True).first()
        
        if not kb:
            return []
        
        # Generate embedding for query
        llm_client = get_llm_client()
        query_embedding = llm_client.embed(query)
        
        # Get vector DB connector
        connector = get_vector_db_connector(
            vector_db_type=kb.vector_db_type,
            collection_name=kb.collection_name
        )
        connector.connect()
        
        # Perform search
        results = connector.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter=filter
        )
        
        return results
    
    def semantic_filter(self, query: str, **kwargs):
        """
        Filter queryset using semantic search results.
        This is a placeholder - actual implementation would require
        matching semantic search results back to model instances.
        """
        # This would require storing document IDs in the vector DB
        # and mapping them back to model instances
        results = self.semantic_search(query, **kwargs)
        # For now, return original queryset
        # In a full implementation, you'd filter based on result IDs
        return self


class SemanticSearchQuerySet(models.QuerySet, SemanticSearchMixin):
    """QuerySet with semantic search capabilities"""
    pass


"""
Vector database connector utilities for RAG system.
Supports ChromaDB, Qdrant, and PGVector.
"""
from typing import List, Dict, Any, Optional
from django.conf import settings
import os

from ..settings import (
    DJANGO_FORGE_AI_VECTOR_DB,
    DJANGO_FORGE_AI_VECTOR_DB_PATH,
    DJANGO_FORGE_AI_CHROMA_HOST,
    DJANGO_FORGE_AI_CHROMA_PORT,
    DJANGO_FORGE_AI_QDRANT_HOST,
    DJANGO_FORGE_AI_QDRANT_PORT,
    DJANGO_FORGE_AI_QDRANT_COLLECTION,
)


class VectorDBConnector:
    """
    Abstract base class for vector database connectors.
    """
    
    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name
        self._client = None
    
    def connect(self):
        """Initialize connection to vector database"""
        raise NotImplementedError
    
    def add_embeddings(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add embeddings to the vector database"""
        raise NotImplementedError
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        raise NotImplementedError
    
    def delete(self, ids: List[str]):
        """Delete embeddings by IDs"""
        raise NotImplementedError
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        raise NotImplementedError


class ChromaDBConnector(VectorDBConnector):
    """ChromaDB connector implementation"""
    
    def __init__(self, collection_name: str = "default", path: Optional[str] = None):
        super().__init__(collection_name)
        self.path = path or DJANGO_FORGE_AI_VECTOR_DB_PATH
        self._client = None
        self._collection = None
    
    def connect(self):
        """Initialize ChromaDB connection"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Use persistent client if path is provided
            if self.path:
                self._client = chromadb.PersistentClient(
                    path=self.path,
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                # Try to connect to remote ChromaDB
                self._client = chromadb.HttpClient(
                    host=DJANGO_FORGE_AI_CHROMA_HOST,
                    port=DJANGO_FORGE_AI_CHROMA_PORT
                )
            
            # Get or create collection
            try:
                self._collection = self._client.get_collection(name=self.collection_name)
            except Exception:
                self._collection = self._client.create_collection(name=self.collection_name)
                
        except ImportError:
            raise ImportError("ChromaDB not installed. Install with: pip install chromadb")
    
    def add_embeddings(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add embeddings to ChromaDB"""
        if not self._collection:
            self.connect()
        
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        self._collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search ChromaDB"""
        if not self._collection:
            self.connect()
        
        where = filter if filter else None
        
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i] if results['documents'] else '',
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None,
                })
        
        return formatted_results
    
    def delete(self, ids: List[str]):
        """Delete from ChromaDB"""
        if not self._collection:
            self.connect()
        
        self._collection.delete(ids=ids)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection info"""
        if not self._collection:
            self.connect()
        
        count = self._collection.count()
        return {
            'name': self.collection_name,
            'count': count,
            'type': 'chroma'
        }


class QdrantConnector(VectorDBConnector):
    """Qdrant connector implementation"""
    
    def __init__(self, collection_name: str = "default"):
        super().__init__(collection_name)
        self._client = None
        self._collection = None
    
    def connect(self):
        """Initialize Qdrant connection"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self._client = QdrantClient(
                host=DJANGO_FORGE_AI_QDRANT_HOST,
                port=DJANGO_FORGE_AI_QDRANT_PORT
            )
            
            # Check if collection exists, create if not
            collections = self._client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection with default vector size (1536 for OpenAI embeddings)
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,
                        distance=Distance.COSINE
                    )
                )
            
            self._collection = self.collection_name
            
        except ImportError:
            raise ImportError("Qdrant client not installed. Install with: pip install qdrant-client")
    
    def add_embeddings(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add embeddings to Qdrant"""
        if not self._client:
            self.connect()
        
        from qdrant_client.models import PointStruct
        
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        points = []
        for i, (embedding, text, metadata, point_id) in enumerate(zip(embeddings, texts, metadatas, ids)):
            full_metadata = {**metadata, 'text': text}
            points.append(
                PointStruct(
                    id=i,
                    vector=embedding,
                    payload=full_metadata
                )
            )
        
        self._client.upsert(
            collection_name=self._collection,
            points=points
        )
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search Qdrant"""
        if not self._client:
            self.connect()
        
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        query_filter = None
        if filter:
            conditions = [
                FieldCondition(key=key, match=MatchValue(value=value))
                for key, value in filter.items()
            ]
            if conditions:
                query_filter = Filter(must=conditions)
        
        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=query_filter
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': str(result.id),
                'text': result.payload.get('text', ''),
                'metadata': {k: v for k, v in result.payload.items() if k != 'text'},
                'distance': result.score,
            })
        
        return formatted_results
    
    def delete(self, ids: List[str]):
        """Delete from Qdrant"""
        if not self._client:
            self.connect()
        
        int_ids = []
        for id_str in ids:
            try:
                int_ids.append(int(id_str))
            except ValueError:
                continue
        
        if int_ids:
            self._client.delete(
                collection_name=self._collection,
                points_selector=int_ids
            )
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection info"""
        if not self._client:
            self.connect()
        
        collection_info = self._client.get_collection(self._collection)
        return {
            'name': self._collection,
            'count': collection_info.points_count,
            'type': 'qdrant'
        }


class PGVectorConnector(VectorDBConnector):
    """PGVector connector implementation (requires django.contrib.postgres)"""
    
    def __init__(self, collection_name: str = "default"):
        super().__init__(collection_name)
        self._connection = None
    
    def connect(self):
        """Initialize PGVector connection"""
        from django.db import connection
        from django.contrib.postgres.operations import CreateExtension
        
        self._connection = connection
        
        # Ensure pgvector extension is installed
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    def add_embeddings(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add embeddings to PGVector"""
        if not self._connection:
            self.connect()
        
        # This would require a custom model with pgvector field
        # For now, raise NotImplementedError
        raise NotImplementedError(
            "PGVector integration requires custom Django models with pgvector fields. "
            "See Django documentation for pgvector integration."
        )
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search PGVector"""
        raise NotImplementedError("PGVector search not yet implemented")
    
    def delete(self, ids: List[str]):
        """Delete from PGVector"""
        raise NotImplementedError("PGVector delete not yet implemented")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection info"""
        return {'name': self.collection_name, 'type': 'pgvector'}


def get_vector_db_connector(
    vector_db_type: Optional[str] = None,
    collection_name: str = "default"
) -> VectorDBConnector:
    """
    Factory function to get appropriate vector DB connector.
    
    Args:
        vector_db_type: Type of vector DB ('chroma', 'qdrant', 'pgvector')
        collection_name: Name of the collection
    
    Returns:
        VectorDBConnector instance
    """
    vector_db_type = vector_db_type or DJANGO_FORGE_AI_VECTOR_DB
    
    if vector_db_type == 'chroma':
        return ChromaDBConnector(collection_name=collection_name)
    elif vector_db_type == 'qdrant':
        return QdrantConnector(collection_name=collection_name)
    elif vector_db_type == 'pgvector':
        return PGVectorConnector(collection_name=collection_name)
    else:
        raise ValueError(f"Unsupported vector DB type: {vector_db_type}")


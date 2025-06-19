"""
Celery tasks for async AI operations.
"""
from celery import shared_task
from typing import List
import os

from .rag_system.models import Document, DocumentChunk
from .rag_system.vector_utils import get_vector_db_connector
from .utils.llm_client import get_llm_client
from .agents.orchestrator import execute_agent_task
from .settings import (
    DJANGO_FORGE_AI_RAG_CHUNK_SIZE,
    DJANGO_FORGE_AI_RAG_CHUNK_OVERLAP,
)


@shared_task
def generate_embeddings_task(document_id: int):
    """
    Generate embeddings for a document and store in vector database.
    
    Args:
        document_id: ID of the Document to process
    """
    try:
        document = Document.objects.get(pk=document_id)
        document.embedding_status = 'processing'
        document.save()
        
        # Get knowledge base
        kb = document.knowledge_base
        
        # Chunk the document
        chunks = _chunk_text(
            document.content,
            chunk_size=DJANGO_FORGE_AI_RAG_CHUNK_SIZE,
            chunk_overlap=DJANGO_FORGE_AI_RAG_CHUNK_OVERLAP
        )
        
        # Generate embeddings
        llm_client = get_llm_client()
        embeddings = []
        chunk_objects = []
        
        for i, chunk_text in enumerate(chunks):
            embedding = llm_client.embed(chunk_text)
            embeddings.append(embedding)
            
            # Create chunk object
            chunk_obj = DocumentChunk.objects.create(
                document=document,
                chunk_index=i,
                content=chunk_text,
                start_char=i * DJANGO_FORGE_AI_RAG_CHUNK_SIZE,
                end_char=min((i + 1) * DJANGO_FORGE_AI_RAG_CHUNK_SIZE, len(document.content)),
                embedding=embedding,
                metadata={'chunk_index': i}
            )
            chunk_objects.append(chunk_obj)
        
        # Store in vector database
        connector = get_vector_db_connector(
            vector_db_type=kb.vector_db_type,
            collection_name=kb.collection_name
        )
        connector.connect()
        
        # Prepare data for vector DB
        texts = [chunk.content for chunk in chunk_objects]
        metadatas = [
            {
                'document_id': document.id,
                'document_title': document.title,
                'chunk_index': chunk.chunk_index,
                **chunk.metadata
            }
            for chunk in chunk_objects
        ]
        ids = [f"doc_{document.id}_chunk_{chunk.chunk_index}" for chunk in chunk_objects]
        
        connector.add_embeddings(
            embeddings=embeddings,
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        # Update document status
        document.is_embedded = True
        document.embedding_status = 'completed'
        document.chunk_count = len(chunks)
        document.save()
        
        return f"Successfully generated embeddings for {len(chunks)} chunks"
        
    except Exception as e:
        document.embedding_status = 'failed'
        document.save()
        raise


def _chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move start position with overlap
        start = end - chunk_overlap
        if start >= len(text):
            break
    
    return chunks


@shared_task
def execute_agent_task_async(task_id: int):
    """
    Execute an agent task asynchronously.
    
    Args:
        task_id: ID of the AgentTask to execute
    """
    try:
        result = execute_agent_task(task_id)
        return result
    except Exception as e:
        raise


@shared_task
def process_url_document(url: str, knowledge_base_id: int):
    """
    Fetch content from URL and create a document.
    
    Args:
        url: URL to fetch content from
        knowledge_base_id: ID of the knowledge base
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Fetch URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text
        title = soup.find('title')
        title_text = title.get_text() if title else "Untitled"
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        content = soup.get_text()
        content = ' '.join(content.split())  # Clean up whitespace
        
        # Create document
        from .rag_system.models import KnowledgeBase
        kb = KnowledgeBase.objects.get(pk=knowledge_base_id)
        
        document = Document.objects.create(
            knowledge_base=kb,
            title=title_text,
            content=content,
            source_type='url',
            source_url=url
        )
        
        # Trigger embedding generation
        generate_embeddings_task.delay(document.id)
        
        return f"Successfully processed URL: {url}"
        
    except Exception as e:
        raise


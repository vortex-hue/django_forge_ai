"""
Pydantic schemas for validating LLM outputs and structured data.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class ContentGenerationRequest(BaseModel):
    """Schema for content generation requests"""
    prompt: str = Field(..., description="The generation prompt")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_length: Optional[int] = Field(None, description="Maximum length of generated content")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    
    class Config:
        extra = "forbid"


class ContentGenerationResponse(BaseModel):
    """Schema for content generation responses"""
    content: str = Field(..., description="Generated content")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    model: Optional[str] = Field(None, description="Model used for generation")
    
    class Config:
        extra = "forbid"


class ModerationResult(BaseModel):
    """Schema for content moderation results"""
    flagged: bool = Field(..., description="Whether content was flagged")
    categories: Dict[str, bool] = Field(default_factory=dict, description="Category flags")
    category_scores: Dict[str, float] = Field(default_factory=dict, description="Category scores")
    reason: Optional[str] = Field(None, description="Reason for flagging")
    
    class Config:
        extra = "forbid"


class EmbeddingRequest(BaseModel):
    """Schema for embedding generation requests"""
    text: str = Field(..., description="Text to embed")
    model: Optional[str] = Field(None, description="Embedding model to use")
    
    class Config:
        extra = "forbid"


class EmbeddingResponse(BaseModel):
    """Schema for embedding responses"""
    embedding: List[float] = Field(..., description="Embedding vector")
    model: str = Field(..., description="Model used")
    dimensions: int = Field(..., description="Embedding dimensions")
    
    class Config:
        extra = "forbid"


class AgentConfigSchema(BaseModel):
    """Schema for agent configuration"""
    name: str = Field(..., description="Agent name")
    persona: str = Field(..., description="Agent persona/description")
    goals: List[str] = Field(default_factory=list, description="Agent goals")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_iterations: int = Field(10, ge=1, le=100, description="Maximum iterations")
    
    class Config:
        extra = "forbid"


class AgentTaskRequest(BaseModel):
    """Schema for agent task requests"""
    agent_id: int = Field(..., description="Agent ID")
    task_description: str = Field(..., description="Task to execute")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    class Config:
        extra = "forbid"


class AgentTaskResponse(BaseModel):
    """Schema for agent task responses"""
    task_id: int = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    result: Optional[str] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        extra = "forbid"


class RAGQueryRequest(BaseModel):
    """Schema for RAG query requests"""
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, ge=1, le=100, description="Number of results to return")
    filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    
    class Config:
        extra = "forbid"


class RAGQueryResponse(BaseModel):
    """Schema for RAG query responses"""
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    query: str = Field(..., description="Original query")
    total_results: int = Field(..., description="Total number of results")
    
    class Config:
        extra = "forbid"


"""
API models for the Restaurant Chat API.

This module contains all the Pydantic models used for request/response validation
and documentation in the API. Each model includes detailed field descriptions
and examples to make the API more user-friendly.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Base models
class QueryRequest(BaseModel):
    """Request model for simple restaurant queries"""
    query: str = Field(
        ...,
        min_length=1,
        description="The search query to find restaurant information",
        example="Italian restaurants in downtown with outdoor seating"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Italian restaurants in downtown with outdoor seating"
            }
        }

class QueryResult(BaseModel):
    """Result from a restaurant query"""
    restaurant: str = Field(..., description="Name of the restaurant")
    rating: str = Field(..., description="Restaurant rating")
    price_range: str = Field(..., description="Price range of the restaurant")
    description: str = Field(..., description="Description of the restaurant")
    score: float = Field(..., description="Relevance score of the result")

class QueryResponse(BaseModel):
    """Response containing query results"""
    results: List[QueryResult] = Field(default_factory=list, description="List of query results")

# Restaurant models
class MenuItem(BaseModel):
    """Model for menu items"""
    name: str = Field(
        ...,
        description="Name of the menu item",
        example="Homemade Lasagna"
    )
    restaurant_name: str = Field(
        ...,
        description="Name of the restaurant",
        example="La Bella Italia"
    )
    category: Optional[str] = Field(
        None,
        description="Category of the menu item",
        example="Pasta"
    )
    relevance_score: float = Field(
        ...,
        description="Relevance score from search",
        example=0.95
    )

class MenuSection(BaseModel):
    """Model for a menu section"""
    name: str = Field(
        ...,
        description="Name of the menu section",
        example="Pasta"
    )
    items: List[MenuItem] = Field(
        default_factory=list,
        description="List of menu items in this section"
    )

class RestaurantInfo(BaseModel):
    """Model for basic restaurant information"""
    name: str = Field(
        ...,
        description="Name of the restaurant",
        example="La Bella Italia"
    )
    rating: Optional[float] = Field(
        None,
        description="Restaurant rating (0-5)",
        example=4.5
    )
    price_range: Optional[str] = Field(
        None,
        description="Price range indicator ($, $$, $$$)",
        example="$$"
    )
    relevance_score: float = Field(
        ...,
        description="Relevance score from search",
        example=0.95
    )

class RestaurantDetails(BaseModel):
    """Model for complete restaurant details"""
    id: str = Field(
        ...,
        description="Unique identifier for the restaurant",
        example="rest_123456789"
    )
    name: str = Field(
        ...,
        description="Name of the restaurant",
        example="La Bella Italia"
    )
    rating: float = Field(
        ...,
        description="Restaurant rating (0-5)",
        example=4.5
    )
    price_range: str = Field(
        ...,
        description="Price range indicator ($, $$, $$$)",
        example="$$"
    )
    description: str = Field(
        ...,
        description="Restaurant description",
        example="Authentic Italian cuisine with a modern twist"
    )
    cuisine_type: str = Field(
        ...,
        description="Type of cuisine",
        example="Italian"
    )
    location: str = Field(
        ...,
        description="Restaurant location",
        example="123 Main St, Downtown"
    )
    popular_dishes: List[str] = Field(
        ...,
        description="List of popular dishes",
        example=["Homemade Lasagna", "Fettuccine Alfredo", "Tiramisu"]
    )

class Restaurant(BaseModel):
    """Model for detailed restaurant information"""
    id: str = Field(
        ...,
        description="Unique identifier for the restaurant",
        example="rest_123456789"
    )
    name: str = Field(
        ...,
        description="Name of the restaurant",
        example="La Bella Italia"
    )
    rating: float = Field(
        ...,
        description="Restaurant rating (0-5)",
        example=4.5
    )
    price_range: str = Field(
        ...,
        description="Price range indicator ($, $$, $$$)",
        example="$$"
    )
    description: str = Field(
        ...,
        description="Restaurant description",
        example="Authentic Italian cuisine with a modern twist"
    )
    cuisine_type: Optional[str] = Field(
        None,
        description="Type of cuisine",
        example="Italian"
    )
    location: Optional[str] = Field(
        None,
        description="Restaurant location",
        example="123 Main St, Downtown"
    )
    popular_dishes: Optional[List[str]] = Field(
        None,
        description="List of popular dishes",
        example=["Homemade Lasagna", "Fettuccine Alfredo", "Tiramisu"]
    )

class RestaurantResult(BaseModel):
    """Detailed restaurant search result"""
    restaurant_name: str = Field(..., description="Name of the restaurant")
    rating: float = Field(..., description="Restaurant rating")
    price_range: str = Field(..., description="Price range of the restaurant")
    description: str = Field(..., description="Description of the restaurant")
    score: float = Field(..., description="Relevance score of the result")

class RestaurantSearchRequest(BaseModel):
    """Request for searching restaurants"""
    query: str = Field(..., description="Search query string")
    price_range: Optional[str] = Field(None, description="Filter by price range (e.g. $, $$, $$$)")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(default=10, ge=1, le=50, description="Number of results per page")

class RestaurantSearchResponse(BaseModel):
    """Response containing restaurant search results"""
    restaurants: List[RestaurantResult] = Field(default_factory=list, description="List of restaurant results")
    total_results: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of results per page")

class RestaurantSearchParams(BaseModel):
    """Parameters for searching restaurants"""
    query: Optional[str] = Field(
        None,
        description="Search query text",
        example="Italian restaurants with outdoor seating"
    )
    cuisine_type: Optional[str] = Field(
        None,
        description="Filter by cuisine type",
        example="Italian"
    )
    min_rating: Optional[float] = Field(
        None,
        ge=0,
        le=5,
        description="Minimum rating filter (0-5)",
        example=4.0
    )
    price_range: Optional[str] = Field(
        None,
        description="Filter by price range",
        example="$$"
    )
    page: Optional[int] = Field(
        1,
        ge=1,
        description="Page number for pagination",
        example=1
    )
    page_size: Optional[int] = Field(
        10,
        ge=1,
        le=50,
        description="Number of results per page",
        example=10
    )
    sort_by: Optional[str] = Field(
        "relevance",
        description="Sort results by: relevance, rating, or name",
        example="rating"
    )
    sort_order: Optional[str] = Field(
        "desc",
        description="Sort order: asc or desc",
        example="desc"
    )

    @validator("price_range")
    def validate_price_range(cls, v):
        """Validate that price range contains only $ symbols"""
        if v is not None and not all(c == "$" for c in v):
            raise ValueError("Price range must contain only $ symbols")
        return v

# Chat models
class ChatRequest(BaseModel):
    """Request for chat completion"""
    query: str = Field(..., description="User's chat message")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation")
    context_window_size: int = Field(default=5, description="Number of previous messages to include as context")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the conversation",
        example={"user_id": "123", "session_id": "abc"}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the best Italian restaurants?",
                "conversation_id": "abc123",
                "context_window_size": 5,
                "metadata": {
                    "user_id": "123",
                    "session_id": "abc"
                }
            }
        }

class ChatResponse(BaseModel):
    """Response from chat completion"""
    response: str = Field(..., description="Generated chat response")
    conversation_id: str = Field(..., description="ID of the conversation")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the response",
        example={
            "response_time": 0.8,
            "tokens_used": 150,
            "context_chunks": 3
        }
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Our most popular dishes include the homemade lasagna and the fettuccine alfredo.",
                "conversation_id": "conv_123456789",
                "metadata": {
                    "response_time": 0.8,
                    "tokens_used": 150,
                    "context_chunks": 3
                }
            }
        }

class ConversationMetadata(BaseModel):
    """Model for conversation metadata"""
    created_at: float = Field(
        ...,
        description="Unix timestamp when the conversation was created",
        example=1638360000.0
    )
    last_updated: float = Field(
        ...,
        description="Unix timestamp when the conversation was last updated",
        example=1638360100.0
    )
    message_count: int = Field(
        ...,
        description="Number of messages in the conversation",
        example=10
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the conversation",
        example={
            "user_id": "user_123",
            "total_tokens": 1500,
            "language": "en"
        }
    )

class Message(BaseModel):
    """Model for chat messages"""
    role: str = Field(
        ...,
        description="Role of the message sender (user/assistant)",
        example="user"
    )
    content: str = Field(
        ...,
        description="Content of the message",
        example="What are your most popular dishes?"
    )
    timestamp: float = Field(
        ...,
        description="Unix timestamp when the message was sent",
        example=1638360000.0
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the message",
        example={
            "tokens": 10,
            "context_chunks": 3,
            "response_time": 0.5
        }
    )

class Conversation(BaseModel):
    """Model for complete conversations"""
    id: str = Field(
        ...,
        description="Unique identifier for the conversation",
        example="conv_123456789"
    )
    messages: List[Message] = Field(
        default_factory=list,
        description="List of messages in the conversation"
    )
    metadata: ConversationMetadata = Field(
        ...,
        description="Metadata about the conversation"
    )

class ConversationListResponse(BaseModel):
    """Response model for listing conversations"""
    conversations: List[Conversation] = Field(
        ...,
        description="List of conversations"
    )
    total_count: int = Field(
        ...,
        description="Total number of conversations available",
        example=100
    )
    has_more: bool = Field(
        ...,
        description="Whether there are more conversations available",
        example=True
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [{
                    "id": "conv_123456789",
                    "messages": [{
                        "role": "user",
                        "content": "What are the best pasta dishes at La Bella Italia?",
                        "timestamp": 1638360000.0,
                        "metadata": {
                            "tokens": 10,
                            "context_chunks": 3
                        }
                    }, {
                        "role": "assistant",
                        "content": "Our most popular dishes include the homemade lasagna and the fettuccine alfredo.",
                        "timestamp": 1638360000.0,
                        "metadata": {
                            "tokens": 150,
                            "context_chunks": 3
                        }
                    }],
                    "metadata": {
                        "created_at": 1638360000.0,
                        "last_updated": 1638360100.0,
                        "message_count": 2,
                        "metadata": {
                            "user_id": "user_123",
                            "total_tokens": 1500,
                            "language": "en"
                        }
                    }
                }],
                "total_count": 100,
                "has_more": True
            }
        }

# Error models
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "QUERY_PROCESSING_FAILED",
                "message": "Failed to process the query due to invalid input",
                "details": {
                    "invalid_fields": ["query"],
                    "reason": "Query length exceeds maximum limit"
                }
            }
        } 
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    """Request model for simple queries"""
    query: str = Field(..., min_length=1, description="The search query")

class QueryResult(BaseModel):
    restaurant: str
    rating: str
    price_range: str
    description: str
    score: float

class QueryResponse(BaseModel):
    """Response model for queries"""
    results: List[QueryResult]

class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    query: str = Field(..., min_length=1, description="User's query text")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation")
    context_window_size: Optional[int] = Field(5, ge=1, le=10, description="Number of recent messages to include")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the conversation")

class RestaurantInfo(BaseModel):
    """Model for restaurant information"""
    name: str = Field(..., description="Name of the restaurant")
    rating: Optional[float] = Field(None, description="Restaurant rating")
    price_range: Optional[str] = Field(None, description="Price range indicator")
    relevance_score: float = Field(..., description="Relevance score from vector search")

class MenuItem(BaseModel):
    """Model for menu items"""
    name: str = Field(..., description="Name of the menu item")
    restaurant_name: str = Field(..., description="Name of the restaurant")
    category: Optional[str] = Field(None, description="Category of the menu item")
    relevance_score: float = Field(..., description="Relevance score from vector search")

class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    response: str = Field(..., description="Generated response text")
    conversation_id: str = Field(..., description="ID of the conversation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the response")

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str = Field(..., description="Error message")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")

class RestaurantSearchRequest(BaseModel):
    """Parameters for searching restaurants"""
    query: Optional[str] = Field(None, description="Search query for restaurants")
    price_range: Optional[str] = Field(None, description="Price range filter (e.g., $, $$, $$$)")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    page: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(10, ge=1, le=50, description="Number of results per page")
    
    @validator("price_range")
    def validate_price_range(cls, v):
        if v is not None and not all(c == "$" for c in v):
            raise ValueError("Price range must contain only $ symbols")
        return v

class Restaurant(BaseModel):
    """Model for a restaurant"""
    id: str = Field(..., description="Unique identifier for the restaurant")
    name: str = Field(..., description="Name of the restaurant")
    rating: float = Field(..., description="Restaurant rating")
    price_range: str = Field(..., description="Price range indicator")
    description: str = Field(..., description="Restaurant description")
    cuisine_type: Optional[str] = Field(None, description="Type of cuisine")
    location: Optional[str] = Field(None, description="Restaurant location")
    popular_dishes: Optional[List[str]] = Field(None, description="List of popular dishes")

class RestaurantDetails(BaseModel):
    """Restaurant details model"""
    id: str
    name: str
    rating: float
    price_range: str
    description: str
    cuisine_type: str
    location: str
    popular_dishes: List[str]

class RestaurantSearchResponse(BaseModel):
    """Response model for restaurant search"""
    restaurants: List[RestaurantDetails]
    total_results: int
    total_pages: int
    page: int
    page_size: int

class MenuSection(BaseModel):
    """Model for a menu section"""
    name: str = Field(..., description="Name of the menu section")
    items: List[MenuItem] = Field(default_factory=list, description="List of menu items in this section")

class RestaurantSearchParams(BaseModel):
    """Parameters for searching restaurants"""
    query: Optional[str] = Field(None, description="Search query text")
    cuisine_type: Optional[str] = Field(None, description="Filter by cuisine type")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    price_range: Optional[str] = Field(None, description="Filter by price range")
    page: Optional[int] = Field(1, ge=1, description="Page number for pagination")
    page_size: Optional[int] = Field(10, ge=1, le=50, description="Number of results per page")
    sort_by: Optional[str] = Field("relevance", description="Sort results by: relevance, rating, or name")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")

class ConversationMetadata(BaseModel):
    """Model for conversation metadata"""
    created_at: float = Field(..., description="Timestamp when the conversation was created")
    last_updated: float = Field(..., description="Timestamp when the conversation was last updated")
    message_count: int = Field(..., description="Number of messages in the conversation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the conversation")

class Message(BaseModel):
    """Model for chat messages"""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: float = Field(..., description="Timestamp when the message was sent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the message")

class Conversation(BaseModel):
    """Model for complete conversations"""
    id: str = Field(..., description="Unique identifier for the conversation")
    messages: List[Message] = Field(default_factory=list, description="List of messages in the conversation")
    metadata: ConversationMetadata = Field(..., description="Metadata about the conversation")

class ConversationListResponse(BaseModel):
    """Response model for listing conversations"""
    conversations: List[Conversation] = Field(..., description="List of conversations")
    total_count: int = Field(..., description="Total number of conversations")
    has_more: bool = Field(..., description="Whether there are more conversations available") 
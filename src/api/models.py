from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    """Request model for simple queries"""
    query: str = Field(..., description="The user's query text")
    top_k: Optional[int] = Field(3, description="Number of similar results to return")
    score_threshold: Optional[float] = Field(0.7, description="Minimum similarity score to include in results")

class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    query: str = Field(..., description="The user's query text")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation to continue")
    model: Optional[str] = Field("gpt-4-turbo-preview", description="OpenAI model to use")
    temperature: Optional[float] = Field(0.7, description="Response creativity (0.0 to 1.0)")
    max_tokens: Optional[int] = Field(500, description="Maximum response length")

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

class QueryResponse(BaseModel):
    """Response model for queries"""
    restaurants: List[RestaurantInfo] = Field(default_factory=list, description="List of relevant restaurants")
    menu_items: List[MenuItem] = Field(default_factory=list, description="List of relevant menu items")
    total_results: int = Field(..., description="Total number of results found")

class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    response: str = Field(..., description="Generated response text")
    conversation_id: str = Field(..., description="ID of the conversation")
    context: QueryResponse = Field(..., description="Context information used for the response")

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details") 
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

class MenuSection(BaseModel):
    """Model for a menu section"""
    name: str = Field(..., description="Name of the menu section")
    items: List[MenuItem] = Field(default_factory=list, description="List of menu items in this section")

class RestaurantDetails(BaseModel):
    """Detailed restaurant information model"""
    id: str = Field(..., description="Unique identifier for the restaurant")
    name: str = Field(..., description="Name of the restaurant")
    rating: Optional[float] = Field(None, description="Restaurant rating")
    price_range: Optional[str] = Field(None, description="Price range indicator")
    cuisine_type: Optional[str] = Field(None, description="Type of cuisine")
    description: Optional[str] = Field(None, description="Restaurant description")
    menu_sections: List[MenuSection] = Field(default_factory=list, description="Menu sections with items")
    popular_items: List[MenuItem] = Field(default_factory=list, description="Popular menu items")
    relevance_score: Optional[float] = Field(None, description="Search relevance score")

class RestaurantSearchResponse(BaseModel):
    """Response model for restaurant search"""
    restaurants: List[RestaurantDetails] = Field(default_factory=list, description="List of matching restaurants")
    total_results: int = Field(..., description="Total number of matching restaurants")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of results per page")
    total_pages: int = Field(..., description="Total number of pages available") 
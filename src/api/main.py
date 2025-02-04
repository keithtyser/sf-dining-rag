import uuid
import math
import time
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.api.models import (
    QueryRequest,
    ChatRequest,
    QueryResponse,
    ChatResponse,
    ErrorResponse,
    RestaurantInfo,
    MenuItem,
    RestaurantSearchParams,
    RestaurantDetails,
    RestaurantSearchResponse,
    MenuSection,
    QueryResult,
    RestaurantSearchRequest,
    Restaurant
)
from src.api.middleware import RequestLoggingMiddleware, setup_middleware
from src.query import get_similar_chunks
from src.chat import generate_response
from src.conversation import ConversationManager
from src.api.dependencies import get_openai_client, get_pinecone_index
from src.embedding import batch_generate_embeddings, get_embedding
from src.vector_db import init_pinecone, upsert_embeddings, query_similar
from openai import OpenAI
from fastapi.responses import JSONResponse

# API version and prefix
API_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

# Initialize FastAPI app with configuration
app = FastAPI(
    title="Restaurant Chat API",
    description="""
    API for restaurant information and chat interface.
    Features include:
    * Restaurant search with filters
    * Chat interface for restaurant queries
    * Conversation management
    * Rate limiting and authentication
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoint to verify API status"
        },
        {
            "name": "chat",
            "description": "Chat endpoints for natural language interactions"
        },
        {
            "name": "restaurants",
            "description": "Endpoints for searching and retrieving restaurant information"
        },
        {
            "name": "conversations",
            "description": "Endpoints for managing chat conversations"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    headers_enabled=True,  # Enable rate limit headers
    strategy="fixed-window",  # Use fixed window strategy
)
app.state.limiter = limiter

# Add rate limit middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Add rate limit headers to responses"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        if isinstance(e, RateLimitExceeded):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later."
                },
                headers={
                    "Retry-After": "60"
                }
            )
        raise e

# Add exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later."
        },
        headers={
            "Retry-After": "60"
        }
    )

# Store conversation histories
conversation_manager = ConversationManager()

@app.get(
    f"{API_PREFIX}/health",
    tags=["health"],
    summary="Check API health",
    response_description="Returns the current health status of the API"
)
@limiter.limit("60/minute")
async def health_check(request: Request):
    """
    Perform a health check on the API.
    
    This endpoint can be used to:
    * Verify the API is running
    * Check the response time
    * Validate the rate limiter
    
    Returns:
        dict: A dictionary containing the API health status
    """
    return {"status": "healthy", "version": API_VERSION}

@app.post(
    f"{API_PREFIX}/query",
    response_model=QueryResponse,
    tags=["restaurants"],
    summary="Query restaurant information",
    response_description="Returns a list of relevant restaurant information based on the query"
)
@limiter.limit("30/minute")
async def query_restaurants(request: Request, query_request: QueryRequest):
    """
    Search for restaurant information using natural language queries.
    
    This endpoint uses semantic search to find relevant restaurant information based on the query.
    The results are ranked by relevance score.
    
    Args:
        query_request: The search query and optional parameters
        
    Returns:
        QueryResponse: A list of restaurant results with relevance scores
        
    Raises:
        HTTPException: If the query processing fails
    
    Example:
        ```json
        {
            "query": "Italian restaurants with outdoor seating"
        }
        ```
    """
    try:
        results = get_similar_chunks(query_request.query)
        query_results = []
        for result in results:
            query_results.append(QueryResult(
                restaurant=result.get("restaurant", "Unknown"),
                rating=result.get("rating", "N/A"),
                price_range=result.get("price_range", "N/A"),
                description=result.get("description", ""),
                score=result.get("score", 0.0)
            ))
        return QueryResponse(results=query_results)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Query processing failed",
                "message": str(e)
            }
        )

@app.post(
    f"{API_PREFIX}/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Generate chat response",
    response_description="Returns an AI-generated response based on the conversation context"
)
@limiter.limit("30/minute")
async def chat_completion(
    request: Request,
    chat_request: ChatRequest,
    openai_client: OpenAI = Depends(get_openai_client)
):
    """
    Generate a chat response based on the user's query and conversation context.
    
    Args:
        chat_request (ChatRequest): The chat request containing the query and optional conversation ID
        openai_client (OpenAI): The OpenAI client for generating responses
        
    Returns:
        ChatResponse: The generated response and conversation details
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        
        # Generate response
        response = await generate_response(
            query=chat_request.query,
            conversation_id=conversation_id,
            client=openai_client,
            get_similar_chunks=get_similar_chunks,
            context_window_size=chat_request.context_window_size
        )
        
        if not response:
            raise Exception("Failed to generate response")
            
        return ChatResponse(
            response=response,
            conversation_id=conversation_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Chat completion failed",
                "message": str(e)
            }
        )

@app.get(
    f"{API_PREFIX}/conversations/recent",
    response_model=List[Dict[str, Any]],
    tags=["conversations"],
    summary="Get recent conversations",
    response_description="Returns a list of recent conversations"
)
@limiter.limit("60/minute")
async def get_recent_conversations(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of conversations to return")
):
    """
    Retrieve recent conversations from the system.
    
    This endpoint returns the most recent conversations, ordered by last update time.
    Each conversation includes:
    * Conversation ID
    * Message history
    * Metadata
    * Timestamps
    
    Args:
        limit: Maximum number of conversations to return (1-50)
        
    Returns:
        List[Dict[str, Any]]: List of recent conversations
        
    Raises:
        HTTPException: If fetching conversations fails
    """
    try:
        conversations = conversation_manager.get_recent_conversations(limit=limit)
        return [conv.to_dict() for conv in conversations]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch recent conversations",
                "message": str(e)
            }
        )

@app.delete(
    f"{API_PREFIX}/conversations/cleanup",
    tags=["conversations"],
    summary="Clean up old conversations",
    response_description="Returns the status of the cleanup operation"
)
@limiter.limit("10/minute")
async def cleanup_old_conversations(
    request: Request,
    days_old: int = Query(30, ge=1, description="Age in days of conversations to clean up")
):
    """
    Remove conversations older than the specified number of days.
    
    This endpoint:
    * Removes old conversations from storage
    * Frees up system resources
    * Helps maintain system performance
    
    Args:
        days_old: Age in days of conversations to remove (minimum 1)
        
    Returns:
        dict: Status of the cleanup operation
        
    Raises:
        HTTPException: If cleanup fails
    """
    try:
        conversation_manager.cleanup_old_conversations(days_old=days_old)
        return {
            "status": "success",
            "message": f"Cleaned up conversations older than {days_old} days"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to clean up conversations",
                "message": str(e)
            }
        )

def process_restaurant_results(results: List[Dict], page: int = 1, page_size: int = 10) -> RestaurantSearchResponse:
    """Process and format restaurant search results"""
    restaurants = []
    restaurant_map = {}
    
    # Group results by restaurant
    for result in results:
        metadata = result.get("metadata", {})
        score = result.get("score", 0)
        
        if metadata.get("type") == "restaurant_overview":
            restaurant_id = metadata.get("restaurant_id", str(uuid.uuid4()))
            
            if restaurant_id not in restaurant_map:
                restaurant_map[restaurant_id] = RestaurantDetails(
                    id=restaurant_id,
                    name=metadata.get("restaurant_name", "Unknown"),
                    rating=metadata.get("rating"),
                    price_range=metadata.get("price_range"),
                    cuisine_type=metadata.get("cuisine_type"),
                    description=metadata.get("description"),
                    relevance_score=score,
                    menu_sections=[],
                    popular_items=[]
                )
        
        elif metadata.get("type") == "menu_item":
            restaurant_id = metadata.get("restaurant_id", "unknown")
            menu_item = MenuItem(
                name=metadata.get("item_name", "Unknown"),
                restaurant_name=metadata.get("restaurant_name", "Unknown"),
                category=metadata.get("category"),
                relevance_score=score
            )
            
            if restaurant_id in restaurant_map:
                # Add to appropriate menu section or create new one
                section_name = metadata.get("category", "Other")
                section = next(
                    (s for s in restaurant_map[restaurant_id].menu_sections if s.name == section_name),
                    None
                )
                
                if section is None:
                    section = MenuSection(name=section_name, items=[])
                    restaurant_map[restaurant_id].menu_sections.append(section)
                
                section.items.append(menu_item)
                
                # Add to popular items if highly relevant
                if score > 0.8:
                    restaurant_map[restaurant_id].popular_items.append(menu_item)
    
    # Convert to list and sort by relevance score
    restaurants = list(restaurant_map.values())
    restaurants.sort(key=lambda x: x.relevance_score or 0, reverse=True)
    
    # Apply pagination
    total_results = len(restaurants)
    total_pages = math.ceil(total_results / page_size)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_restaurants = restaurants[start_idx:end_idx]
    
    return RestaurantSearchResponse(
        restaurants=paginated_restaurants,
        total_results=total_results,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@app.post(f"{API_PREFIX}/restaurants", response_model=RestaurantSearchResponse)
@limiter.limit("30/minute")
async def search_restaurants(request: Request, search_request: RestaurantSearchRequest):
    """Search for restaurants with filters"""
    try:
        # Initialize Pinecone
        index = init_pinecone()
        if not index:
            raise HTTPException(
                status_code=500,
                detail={"error": "database_error", "message": "Failed to connect to vector database"}
            )

        # Get query embedding if query is provided
        query_embedding = None
        if search_request.query:
            query_embedding = await get_embedding(search_request.query)
            if not query_embedding:
                raise HTTPException(
                    status_code=500,
                    detail={"error": "embedding_error", "message": "Failed to generate query embedding"}
                )

        # Prepare filter based on search parameters
        filter_dict = {}
        if search_request.price_range:
            filter_dict["price_range"] = search_request.price_range
        if search_request.min_rating:
            filter_dict["rating"] = {"$gte": search_request.min_rating}

        # Query similar restaurants
        if query_embedding:
            results = query_similar(
                index=index,
                query_embedding=query_embedding,
                top_k=50,  # Get more results for filtering
                score_threshold=0.7,
                filter=filter_dict if filter_dict else None
            )
        else:
            # If no query, get all restaurants matching filters
            results = query_similar(
                index=index,
                query_embedding=[0] * 1536,  # Dummy embedding
                top_k=50,
                score_threshold=0,
                filter=filter_dict if filter_dict else None
            )

        # Convert results to RestaurantDetails objects
        restaurants = []
        for result in results:
            metadata = result["metadata"]
            restaurants.append(
                RestaurantDetails(
                    id=result["id"],
                    name=metadata.get("restaurant_name", "Unknown"),
                    rating=float(metadata.get("rating", 0)),
                    price_range=metadata.get("price_range", "$"),
                    description=metadata.get("description", ""),
                    cuisine_type=metadata.get("cuisine_type", "Unknown"),
                    location=metadata.get("location", "Unknown"),
                    popular_dishes=metadata.get("popular_dishes", [])
                )
            )

        # Apply pagination
        total_results = len(restaurants)
        total_pages = (total_results + search_request.page_size - 1) // search_request.page_size
        start = (search_request.page - 1) * search_request.page_size
        end = start + search_request.page_size
        paginated = restaurants[start:end]

        return RestaurantSearchResponse(
            restaurants=paginated,
            total_results=total_results,
            total_pages=total_pages,
            page=search_request.page,
            page_size=search_request.page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "search_error", "message": f"Error searching restaurants: {str(e)}"}
        )

@app.get(f"{API_PREFIX}/restaurants/{{restaurant_id}}", response_model=RestaurantDetails, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
@limiter.limit("30/minute")
async def get_restaurant_details(request: Request, restaurant_id: str):
    """
    Get detailed information about a specific restaurant
    
    This endpoint returns comprehensive information about a restaurant,
    including its menu sections and popular items.
    """
    try:
        # Search for restaurant by ID
        results = get_similar_chunks(
            f"restaurant {restaurant_id}",
            top_k=20  # Get enough results to build complete profile
        )
        
        # Process results
        response = process_restaurant_results([r for r in results if r.get("metadata", {}).get("restaurant_id") == restaurant_id])
        
        if not response.restaurants:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="Restaurant not found",
                    code="NOT_FOUND",
                    details={"restaurant_id": restaurant_id}
                ).dict()
            )
        
        return response.restaurants[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Failed to get restaurant details",
                code="DETAILS_FAILED",
                details={"message": str(e)}
            ).dict()
        )

@app.get(
    f"{API_PREFIX}/chat/{{conversation_id}}",
    tags=["chat"],
    summary="Get conversation by ID",
    response_description="Returns the conversation details",
    responses={
        404: {"description": "Conversation not found"},
        200: {"description": "Conversation details"}
    }
)
@limiter.limit("60/minute")
async def get_conversation(request: Request, conversation_id: str):
    """
    Retrieve a conversation by its ID.
    
    Args:
        conversation_id (str): The ID of the conversation to retrieve
        
    Returns:
        dict: The conversation details including messages and metadata
    """
    try:
        if conversation_id not in conversation_manager.conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        conv = conversation_manager.get_conversation(conversation_id)
        return {
            "conversation_id": conv.id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in conv.messages
            ],
            "metadata": conv.metadata,
            "created_at": conv.created_at,
            "last_updated": conv.last_updated
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post(
    f"{API_PREFIX}/chat/cleanup",
    tags=["chat"],
    summary="Clean up old conversations",
    response_description="Returns the cleanup status"
)
@limiter.limit("10/minute")
async def cleanup_conversations(request: Request, days_old: int = 30):
    """
    Clean up conversations older than the specified number of days.
    
    Args:
        days_old (int): Number of days after which conversations should be cleaned up
        
    Returns:
        dict: Status of the cleanup operation
    """
    try:
        conversation_manager.cleanup_old_conversations(days_old=days_old)
        return {"status": "success", "message": "Old conversations cleaned up"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
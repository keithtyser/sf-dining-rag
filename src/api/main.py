import uuid
import math
import time
import json
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Request, Body, Response, WebSocket, WebSocketDisconnect
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
    Restaurant,
    RestaurantResult
)
from src.api.middleware import RequestLoggingMiddleware, setup_middleware
from src.query import get_similar_chunks
from src.chat import generate_response
from src.conversation import ConversationManager, get_conversation_history, save_conversation
from src.api.dependencies import (
    get_rate_limiter,
    get_chat_rate_limiter,
    get_cleanup_rate_limiter,
    get_default_rate_limiter,
    limiter,
    get_openai_client
)
from src.embedding import batch_generate_embeddings, get_embedding
from src.vector_db import init_pinecone, upsert_embeddings, query_similar
from openai import OpenAI
from fastapi.responses import JSONResponse
import logging

# Set up logging
logger = logging.getLogger(__name__)

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
    default_limits=["60/minute"],  # Default limit for all endpoints
    headers_enabled=True,  # Enable rate limit headers
    strategy="fixed-window",  # Use fixed window strategy
)
app.state.limiter = limiter

# Rate limit configurations for different endpoints
CHAT_RATE_LIMIT = "30/minute"  # Chat endpoints
CONVERSATION_RATE_LIMIT = "60/minute"  # Conversation management endpoints
CLEANUP_RATE_LIMIT = "10/minute"  # Cleanup endpoint

# Retry times in seconds for different endpoint types
CHAT_RETRY_TIME = 30
CONVERSATION_RETRY_TIME = 45
CLEANUP_RETRY_TIME = 60  # Updated from 30 to 60 seconds

# Add rate limit middleware with enhanced error handling
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Add rate limit headers and handle rate limiting"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        if isinstance(e, RateLimitExceeded):
            retry_after = CLEANUP_RETRY_TIME  # Default retry time
            endpoint_type = "unknown"
            
            # Determine endpoint type for custom retry times
            path = request.url.path
            if "/chat" in path and "cleanup" not in path:
                retry_after = CHAT_RETRY_TIME
                endpoint_type = "chat"
            elif "/conversations" in path:
                retry_after = CONVERSATION_RETRY_TIME
                endpoint_type = "conversation"
            elif "/cleanup" in path:
                retry_after = CLEANUP_RETRY_TIME
                endpoint_type = "cleanup"
            
            return Response(
                content=json.dumps({
                    "detail": {
                        "error": "rate_limit_exceeded",
                        "message": f"Too many requests to {endpoint_type} endpoint. Please try again later.",
                        "endpoint_type": endpoint_type,
                        "retry_after": retry_after
                    }
                }),
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )
        return Response(
            content=json.dumps({
                "detail": {
                    "error": "internal_server_error",
                    "message": str(e)
                }
            }),
            status_code=500,
            media_type="application/json"
        )

# Add exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    retry_after = CLEANUP_RETRY_TIME  # Default retry time
    endpoint_type = "unknown"
    
    # Determine endpoint type for custom retry times
    path = request.url.path
    if "/chat" in path and "cleanup" not in path:
        retry_after = CHAT_RETRY_TIME
        endpoint_type = "chat"
    elif "/conversations" in path:
        retry_after = CONVERSATION_RETRY_TIME
        endpoint_type = "conversation"
    elif "/cleanup" in path:
        retry_after = CLEANUP_RETRY_TIME
        endpoint_type = "cleanup"
    
    return JSONResponse(
        status_code=429,
        content={
            "detail": {
                "error": "rate_limit_exceeded",
                "message": f"Too many requests to {endpoint_type} endpoint. Please try again later.",
                "endpoint_type": endpoint_type,
                "retry_after": retry_after
            }
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Reset": str(int(time.time()) + retry_after)
        }
    )

# Store conversation histories
conversation_manager = ConversationManager()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:  # Create a copy of the list
            try:
                await connection.send_json(message)
            except:
                # Remove failed connections
                self.disconnect(connection)

    async def send_pipeline_update(self, stage: str, status: str, progress: float = 0, data: dict = None):
        message = {
            "type": f"{stage}_{status}",
            "data": {
                "progress": progress,
                **(data or {})
            },
            "timestamp": time.time()
        }
        await self.broadcast(message)

manager = ConnectionManager()

async def process_query_with_rag(query: str, websocket: WebSocket = None):
    """Process a query using the RAG pipeline with real-time updates"""
    try:
        # Retrieval stage
        await manager.send_pipeline_update("retrieval", "start")
        chunks = await get_similar_chunks(query)
        await manager.send_pipeline_update("retrieval", "progress", 50)
        
        # Sort and process chunks
        chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        formatted_chunks = [
            {
                "content": chunk.get("text", ""),
                "tokens": len(chunk.get("text", "").split()),  # Simple token count
                "title": chunk.get("metadata", {}).get("title", "Menu Item"),
                "source": chunk.get("metadata", {}).get("source", "menu"),
                "position": idx + 1,
                "similarity": chunk.get("score", 0)
            }
            for idx, chunk in enumerate(chunks[:5])  # Send top 5 chunks
        ]
        
        await manager.send_pipeline_update("retrieval", "complete", 100, {
            "chunks": formatted_chunks
        })

        return chunks

    except Exception as e:
        await manager.send_pipeline_update("error", "error", data={"message": str(e)})
        raise

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "query":
                await process_query_with_rag(data.get("query", ""), websocket)
            else:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Unsupported message type"},
                    "timestamp": time.time()
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
                "timestamp": time.time()
            })
        except:
            pass
        manager.disconnect(websocket)

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
@get_default_rate_limiter()
async def query_endpoint(request: Request, query_request: QueryRequest):
    """Process a query and return relevant results"""
    try:
        if not query_request.query.strip():
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "validation_error",
                    "message": "Query cannot be empty"
                }
            )

        chunks = await get_similar_chunks(query_request.query)
        results = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if metadata.get("type") == "restaurant_overview":
                result = QueryResult(
                    restaurant=metadata.get("restaurant_name", "Unknown"),
                    rating=str(metadata.get("rating", "N/A")),
                    price_range=metadata.get("price_range", "N/A"),
                    description=metadata.get("text", ""),
                    score=chunk.get("score", 0.0)
                )
                results.append(result)

        return QueryResponse(results=results)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "query_processing_failed",
                "message": str(e)
            }
        )

@app.post(
    f"{API_PREFIX}/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Process a chat message"
)
@get_chat_rate_limiter()
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    openai_client: OpenAI = Depends(get_openai_client)
):
    """Process a chat message and return a response"""
    try:
        # Process query through RAG pipeline
        chunks = await get_similar_chunks(chat_request.query)
        chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Format chunks for frontend
        formatted_chunks = [
            {
                "content": chunk.get("text", ""),
                "tokens": len(chunk.get("text", "").split()),
                "title": chunk.get("metadata", {}).get("title", "Menu Item"),
                "source": chunk.get("metadata", {}).get("source", "menu"),
                "position": idx + 1,
                "similarity": chunk.get("score", 0)
            }
            for idx, chunk in enumerate(chunks[:5])  # Send top 5 chunks
        ]
        
        # Get conversation history
        history = await get_conversation_history(chat_request.conversation_id)
        
        # Generate response
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        response = await generate_response(
            query=chat_request.query,
            conversation_id=conversation_id,
            client=openai_client,
            get_similar_chunks=get_similar_chunks
        )
        
        # Save conversation
        await save_conversation(conversation_id, chat_request.query, response)
        
        return JSONResponse(content={
            "response": response,
            "conversation_id": conversation_id,
            "context_chunks": formatted_chunks
        })

    except HTTPException as e:
        await manager.send_pipeline_update("error", "error", data={"message": str(e)})
        raise e
    except Exception as e:
        await manager.send_pipeline_update("error", "error", data={"message": str(e)})
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "chat_processing_failed",
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
        return JSONResponse(content=[conv.to_dict() for conv in conversations])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch recent conversations",
                "message": str(e)
            }
        )

@app.post(
    f"{API_PREFIX}/conversations/cleanup",
    tags=["conversations"],
    summary="Clean up old conversations",
    response_description="Returns the status of the cleanup operation"
)
@limiter.limit(CLEANUP_RATE_LIMIT)
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

@app.post(
    f"{API_PREFIX}/restaurants",
    response_model=RestaurantSearchResponse,
    tags=["restaurants"],
    summary="Search for restaurants",
    response_description="Returns a list of restaurants matching the search criteria"
)
@get_default_rate_limiter()
async def restaurants_endpoint(request: Request, search_request: RestaurantSearchRequest):
    """Search for restaurants based on criteria"""
    try:
        # Get restaurant results
        chunks = await get_similar_chunks(search_request.query)
        
        # Filter results based on criteria
        filtered_results = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if metadata.get("type") != "restaurant_overview":
                continue
                
            if (search_request.price_range and metadata.get("price_range") != search_request.price_range) or \
               (search_request.min_rating and metadata.get("rating", 0) < search_request.min_rating):
                continue
                
            result = RestaurantResult(
                restaurant_name=metadata.get("restaurant_name", "Unknown"),
                rating=metadata.get("rating", 0.0),
                price_range=metadata.get("price_range", "N/A"),
                description=metadata.get("text", ""),
                score=chunk.get("score", 0.0)
            )
            filtered_results.append(result)

        # Paginate results
        start_idx = (search_request.page - 1) * search_request.page_size
        end_idx = start_idx + search_request.page_size
        paginated_results = filtered_results[start_idx:end_idx]
        
        return RestaurantSearchResponse(
            restaurants=paginated_results,
            total_results=len(filtered_results),
            page=search_request.page,
            page_size=search_request.page_size
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing restaurant search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "restaurant_search_failed",
                "message": str(e)
            }
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
    response_description="Returns the status of the cleanup operation"
)
@get_cleanup_rate_limiter()
async def cleanup_conversations(request: Request, cleanup_request: dict = Body(...)):
    """Clean up old conversations"""
    try:
        days_old = cleanup_request.get("days_old", 30)
        if not isinstance(days_old, int) or days_old < 1:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "validation_error",
                    "message": "days_old must be a positive integer"
                }
            )
            
        conversation_manager.cleanup_old_conversations(days_old=days_old)
        return {
            "status": "success",
            "message": f"Cleaned up conversations older than {days_old} days"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error cleaning up conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "cleanup_failed",
                "message": str(e)
            }
        ) 
import uuid
import math
from typing import Dict, List, Optional
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
from src.chat import generate_response, ConversationHistory
from src.api.dependencies import get_openai_client, get_pinecone_index
from src.embedding import generate_embedding, batch_generate_embeddings
from src.vector_db import init_pinecone, upsert_embeddings, query_similar
from openai import OpenAI

# API version and prefix
API_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Restaurant Chat API",
    description="API for restaurant information and chat interactions",
    version="1.0.0",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Only compress responses larger than 1KB

# Store conversation histories
conversations: Dict[str, ConversationHistory] = {}

@app.get(f"{API_PREFIX}/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post(f"{API_PREFIX}/query", response_model=QueryResponse)
@limiter.limit("30/minute")
async def query_restaurants(request: Request, query_request: QueryRequest):
    """Query for restaurant information"""
    try:
        # Get similar chunks from vector search
        results = get_similar_chunks(query_request.query)
        
        # Convert results to response format
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

@app.post(f"{API_PREFIX}/chat", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat_completion(
    request: Request,
    chat_request: ChatRequest,
    openai_client: OpenAI = Depends(get_openai_client)
):
    """Generate chat response"""
    try:
        # Get or create conversation history
        conversation_id = chat_request.conversation_id or str(len(conversations))
        if conversation_id not in conversations:
            conversations[conversation_id] = ConversationHistory()
        
        # Generate response
        response = generate_response(
            query=chat_request.query,
            conversation_history=conversations[conversation_id],
            client=openai_client,
            get_similar_chunks=get_similar_chunks
        )
        
        if not response:
            raise Exception("Failed to generate response")
            
        # Add to conversation history
        conversations[conversation_id].add_message("user", chat_request.query)
        conversations[conversation_id].add_message("assistant", response)
        
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
    # Mock restaurant data for testing
    restaurants = [
        RestaurantDetails(
            id="1",
            name="Test Italian Restaurant",
            rating=4.5,
            price_range="$$",
            description="A cozy Italian restaurant with authentic cuisine",
            cuisine_type="Italian",
            location="123 Main St",
            popular_dishes=["Pasta Carbonara", "Margherita Pizza"]
        ),
        RestaurantDetails(
            id="2",
            name="Test Sushi Place",
            rating=4.8,
            price_range="$$$",
            description="High-end sushi restaurant with fresh fish",
            cuisine_type="Japanese",
            location="456 Oak Ave",
            popular_dishes=["Dragon Roll", "Tuna Sashimi"]
        )
    ]

    # Apply filters
    filtered = restaurants
    if search_request.min_rating:
        filtered = [r for r in filtered if r.rating >= search_request.min_rating]
    if search_request.price_range:
        filtered = [r for r in filtered if r.price_range == search_request.price_range]

    # Calculate pagination
    total_results = len(filtered)
    total_pages = (total_results + search_request.page_size - 1) // search_request.page_size
    start = (search_request.page - 1) * search_request.page_size
    end = start + search_request.page_size
    paginated = filtered[start:end]

    return RestaurantSearchResponse(
        restaurants=paginated,
        total_results=total_results,
        total_pages=total_pages,
        page=search_request.page,
        page_size=search_request.page_size
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
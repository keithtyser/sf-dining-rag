import uuid
import math
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.models import (
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
    MenuSection
)
from api.middleware import RequestLoggingMiddleware
from query import get_similar_chunks
from chat import generate_response, ConversationHistory

# API version and prefix
API_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Restaurant Assistant API",
    description="API for querying restaurant information and chatting about restaurants",
    version=API_VERSION,
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

@app.get(f"{API_PREFIX}")
@limiter.limit("10/minute")
async def root(request: Request):
    """Root endpoint returning API information"""
    return {
        "name": "Restaurant Assistant API",
        "version": API_VERSION,
        "status": "operational"
    }

@app.post(f"{API_PREFIX}/query", response_model=QueryResponse, responses={400: {"model": ErrorResponse}})
@limiter.limit("30/minute")
async def query_restaurants(request: Request, query_request: QueryRequest):
    """
    Query for restaurant information
    
    This endpoint searches for restaurants and menu items based on the query text.
    Results are ranked by relevance to the query.
    """
    try:
        # Get similar chunks from vector search
        results = get_similar_chunks(
            query_request.query,
            top_k=query_request.top_k,
            score_threshold=query_request.score_threshold
        )
        
        # Process results into response format
        restaurants = []
        menu_items = []
        
        for result in results:
            metadata = result.get("metadata", {})
            score = result.get("score", 0)
            
            if metadata.get("type") == "restaurant_overview":
                restaurants.append(RestaurantInfo(
                    name=metadata.get("restaurant_name", "Unknown"),
                    rating=metadata.get("rating"),
                    price_range=metadata.get("price_range"),
                    relevance_score=score
                ))
            elif metadata.get("type") == "menu_item":
                menu_items.append(MenuItem(
                    name=metadata.get("item_name", "Unknown"),
                    restaurant_name=metadata.get("restaurant_name", "Unknown"),
                    category=metadata.get("category"),
                    relevance_score=score
                ))
        
        return QueryResponse(
            restaurants=restaurants,
            menu_items=menu_items,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Query processing failed",
                code="QUERY_FAILED",
                details={"message": str(e)}
            ).dict()
        )

@app.post(f"{API_PREFIX}/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}})
@limiter.limit("20/minute")
async def chat(request: Request, chat_request: ChatRequest):
    """
    Chat with the restaurant assistant
    
    This endpoint generates responses to user queries using conversation history
    and context from the restaurant database.
    """
    try:
        # Get or create conversation history
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        if conversation_id not in conversations:
            conversations[conversation_id] = ConversationHistory()
        
        # Generate response
        response_text = generate_response(
            query=chat_request.query,
            conversation_history=conversations[conversation_id],
            model=chat_request.model,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens
        )
        
        if not response_text:
            raise Exception("Failed to generate response")
        
        # Get context used for the response
        context_results = get_similar_chunks(chat_request.query, top_k=3)
        
        # Process context results
        restaurants = []
        menu_items = []
        
        for result in context_results:
            metadata = result.get("metadata", {})
            score = result.get("score", 0)
            
            if metadata.get("type") == "restaurant_overview":
                restaurants.append(RestaurantInfo(
                    name=metadata.get("restaurant_name", "Unknown"),
                    rating=metadata.get("rating"),
                    price_range=metadata.get("price_range"),
                    relevance_score=score
                ))
            elif metadata.get("type") == "menu_item":
                menu_items.append(MenuItem(
                    name=metadata.get("item_name", "Unknown"),
                    restaurant_name=metadata.get("restaurant_name", "Unknown"),
                    category=metadata.get("category"),
                    relevance_score=score
                ))
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            context=QueryResponse(
                restaurants=restaurants,
                menu_items=menu_items,
                total_results=len(context_results)
            )
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Chat processing failed",
                code="CHAT_FAILED",
                details={"message": str(e)}
            ).dict()
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

@app.get(f"{API_PREFIX}/restaurants", response_model=RestaurantSearchResponse, responses={400: {"model": ErrorResponse}})
@limiter.limit("30/minute")
async def search_restaurants(request: Request, params: RestaurantSearchParams = Depends()):
    """
    Search for restaurants with filtering and pagination
    
    This endpoint allows searching for restaurants using various criteria
    and returns paginated results with detailed restaurant information.
    """
    try:
        # Build search query
        query_parts = []
        if params.query:
            query_parts.append(params.query)
        if params.cuisine_type:
            query_parts.append(f"cuisine {params.cuisine_type}")
        if params.price_range:
            query_parts.append(f"price range {params.price_range}")
            
        query = " ".join(query_parts) if query_parts else "restaurants"
        
        # Get similar chunks from vector search
        results = get_similar_chunks(
            query,
            top_k=50  # Get more results for filtering
        )
        
        # Filter results
        if params.min_rating is not None:
            results = [
                r for r in results
                if r.get("metadata", {}).get("rating", 0) >= params.min_rating
            ]
        
        # Process and format results
        response = process_restaurant_results(
            results,
            page=params.page,
            page_size=params.page_size
        )
        
        # Sort results if requested
        if params.sort_by != "relevance":
            reverse = params.sort_order == "desc"
            response.restaurants.sort(
                key=lambda x: getattr(x, params.sort_by, 0) or 0,
                reverse=reverse
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Restaurant search failed",
                code="SEARCH_FAILED",
                details={"message": str(e)}
            ).dict()
        )

@app.get(f"{API_PREFIX}/restaurants/{restaurant_id}", response_model=RestaurantDetails, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
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
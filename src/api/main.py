import uuid
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import (
    QueryRequest,
    ChatRequest,
    QueryResponse,
    ChatResponse,
    ErrorResponse,
    RestaurantInfo,
    MenuItem
)
from ..query import get_similar_chunks
from ..chat import generate_response, ConversationHistory

# Create FastAPI app
app = FastAPI(
    title="Restaurant Assistant API",
    description="API for querying restaurant information and chatting about restaurants",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversation histories
conversations: Dict[str, ConversationHistory] = {}

@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {
        "name": "Restaurant Assistant API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/api/query", response_model=QueryResponse, responses={400: {"model": ErrorResponse}})
async def query_restaurants(request: QueryRequest):
    """
    Query for restaurant information
    
    This endpoint searches for restaurants and menu items based on the query text.
    Results are ranked by relevance to the query.
    """
    try:
        # Get similar chunks from vector search
        results = get_similar_chunks(
            request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold
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

@app.post("/api/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}})
async def chat(request: ChatRequest):
    """
    Chat with the restaurant assistant
    
    This endpoint generates responses to user queries using conversation history
    and context from the restaurant database.
    """
    try:
        # Get or create conversation history
        conversation_id = request.conversation_id or str(uuid.uuid4())
        if conversation_id not in conversations:
            conversations[conversation_id] = ConversationHistory()
        
        # Generate response
        response_text = generate_response(
            query=request.query,
            conversation_history=conversations[conversation_id],
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if not response_text:
            raise Exception("Failed to generate response")
        
        # Get context used for the response
        context_results = get_similar_chunks(request.query, top_k=3)
        
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
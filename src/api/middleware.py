import time
import logging
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("restaurant_api")

# Rate limit retry times in seconds
CHAT_RETRY_TIME = 60
CONVERSATION_RETRY_TIME = 60
CLEANUP_RETRY_TIME = 60

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request and response information"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Get request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(f"Request: {method} {url} from {client_host}")
        
        try:
            # Process request and get response
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {method} {url} - Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # Log error
            logger.error(
                f"Error processing {method} {url} - "
                f"Error: {str(e)}"
            )
            raise 

def setup_middleware(app: FastAPI):
    """Set up all middleware for the application"""
    # Add request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return Response(
            status_code=429,
            content={"error": "Rate limit exceeded", "message": str(exc)},
            media_type="application/json"
        ) 

def get_limiter():
    """Get rate limiter instance"""
    return Limiter(key_func=get_remote_address)

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    try:
        # Log request
        logger.info(f"Request: {request.method} {request.url} from {request.client.host}")
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        return response
        
    except RateLimitExceeded as e:
        # Parse error message
        try:
            error_info = json.loads(str(e))
        except json.JSONDecodeError:
            error_info = {"error": "rate_limit_exceeded", "retry_after": 60}
            
        return JSONResponse(
            status_code=429,
            content={"detail": error_info}
        )
            
    except Exception as e:
        # Handle other errors
        logger.error(f"Error processing {request.method} {request.url} - Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "error": "internal_server_error",
                    "message": str(e)
                }
            }
        ) 
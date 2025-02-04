import time
import logging
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("restaurant_api")

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
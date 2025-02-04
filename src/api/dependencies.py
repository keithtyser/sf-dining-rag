"""API dependencies module"""

import os
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import Depends, Request
import pinecone
from src.vector_db import init_pinecone
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Callable

# Load environment variables
load_dotenv()

# Rate limit retry times in seconds
DEFAULT_RETRY_TIME = 60
CHAT_RETRY_TIME = 30
CLEANUP_RETRY_TIME = 60

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@lru_cache()
def get_openai_client() -> OpenAI:
    """Get OpenAI client instance"""
    api_key = os.getenv("OPENAI_API_KEY", "test-key")
    return OpenAI(api_key=api_key)

@lru_cache()
def get_pinecone_api_key() -> str:
    """Get Pinecone API key"""
    return os.getenv("PINECONE_API_KEY", "test-key")

@lru_cache()
def get_pinecone_client():
    """Get Pinecone client instance"""
    api_key = get_pinecone_api_key()
    environment = os.getenv("PINECONE_ENVIRONMENT", "test-env")
    pinecone.init(api_key=api_key, environment=environment)
    return pinecone

def get_pinecone_index():
    """Get initialized Pinecone index"""
    return init_pinecone()

def get_default_rate_limiter() -> Callable:
    """Get default rate limiter decorator"""
    return limiter.limit(
        "60/minute",
        error_message={"error": "rate_limit_exceeded", "retry_after": DEFAULT_RETRY_TIME}
    )

def get_chat_rate_limiter() -> Callable:
    """Get chat endpoint rate limiter decorator"""
    return limiter.limit(
        "30/minute",
        error_message={"error": "rate_limit_exceeded", "retry_after": CHAT_RETRY_TIME}
    )

def get_cleanup_rate_limiter() -> Callable:
    """Get cleanup endpoint rate limiter decorator"""
    return limiter.limit(
        "10/minute",
        error_message={"error": "rate_limit_exceeded", "retry_after": CLEANUP_RETRY_TIME}
    )

def get_rate_limiter() -> Callable:
    """Get rate limiter decorator with correct retry time"""
    return limiter.limit(
        "10/minute",
        error_message={"error": "rate_limit_exceeded", "retry_after": DEFAULT_RETRY_TIME}
    )

# ... existing code ... 
"""API dependencies module"""

import os
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import Depends
import pinecone
from src.vector_db import init_pinecone

# Load environment variables
load_dotenv()

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

# ... existing code ... 
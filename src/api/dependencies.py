import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import Depends
import pinecone
from src.vector_db import init_pinecone

# Load environment variables
load_dotenv(override=True)

def get_openai_client() -> OpenAI:
    """Get OpenAI client with API key from environment"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment")
    return OpenAI(api_key=api_key)

def get_pinecone_index():
    """Get initialized Pinecone index"""
    return init_pinecone()

# ... existing code ... 
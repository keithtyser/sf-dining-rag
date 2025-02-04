from fastapi import Depends
import os
import openai
import pinecone
from src.vector_db import init_pinecone

def get_openai_client():
    """Get OpenAI client instance"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    return openai.OpenAI(api_key=api_key)

def get_pinecone_index():
    """Get Pinecone index instance"""
    return init_pinecone()

# ... existing code ... 
"""
Restaurant Assistant API package
"""

from fastapi import FastAPI
from src.api.main import app
from .models import (
    QueryRequest,
    ChatRequest,
    QueryResponse,
    ChatResponse,
    ErrorResponse,
    RestaurantInfo,
    MenuItem
)

__all__ = ['app'] 
import os
import sys
import uvicorn

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    ) 
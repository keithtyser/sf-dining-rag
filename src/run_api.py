import uvicorn
from api.main import app

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    ) 
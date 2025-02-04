# Restaurant Data RAG Chatbot

A conversational AI chatbot that uses Retrieval-Augmented Generation (RAG) to answer queries about restaurants, menus, and ingredients. The chatbot integrates structured CSV data with unstructured external data and uses OpenAI's GPT-3.5-Turbo for generating responses.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv env
   
   # On Windows:
   .\env\Scripts\activate
   
   # On macOS/Linux:
   source env/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your API keys:
     ```
     OPENAI_API_KEY=your_openai_api_key
     PINECONE_API_KEY=your_pinecone_api_key
     PINECONE_ENVIRONMENT=your_pinecone_environment
     ```

## Project Structure

```
project/
├── data/
│   └── restaurant_data.csv
├── src/
│   ├── ingestion.py      # Data loading and preprocessing
│   ├── chunking.py       # Text chunking utilities
│   ├── embedding.py      # Embedding generation
│   ├── vector_db.py      # Vector database operations
│   ├── query.py          # Query processing
│   └── main.py          # Main application entry point
├── requirements.txt
└── README.md
```

## Usage

1. Place your restaurant data CSV file in the `data/` directory.

2. Run the ingestion pipeline:
   ```bash
   python src/ingestion.py
   ```

3. Start the chatbot:
   ```bash
   python src/main.py
   ```

## Features

- Load and process restaurant data from CSV files
- Fetch additional context from external sources
- Generate embeddings using OpenAI's API
- Store and query vectors using Pinecone
- Process natural language queries
- Generate context-aware responses using GPT-3.5-Turbo

## Development Status

This project is under active development. Check the implementation plan for current progress and upcoming features. 
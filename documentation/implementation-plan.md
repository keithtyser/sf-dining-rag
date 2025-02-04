# Implementation Plan Document: RAG-based Conversational AI Chatbot for Restaurant Data

This document provides a step-by-step guide to implement a conversational AI chatbot using a Retrieval-Augmented Generation (RAG) pipeline. The chatbot will answer queries about restaurants, menus, and ingredients by integrating structured CSV data with unstructured external data and by using OpenAI's GPT-3.5-Turbo for generating responses. Each step includes checkboxes for you to mark off as you complete it.

## Table of Contents

1. [Environment Setup](#environment-setup) ✅
2. [Project Structure Setup](#project-structure-setup) ✅
3. [Data Ingestion Pipeline](#data-ingestion-pipeline) ✅
4. [Text Chunking and Embedding Generation](#text-chunking-and-embedding-generation) ✅
5. [Storing Embeddings in the Vector Database](#storing-embeddings-in-the-vector-database)
6. [Query Processing Pipeline](#query-processing-pipeline)
7. [LLM Integration and Prompt Engineering](#llm-integration-and-prompt-engineering)
8. [Testing and Debugging](#testing-and-debugging)
9. [Deployment](#deployment)
10. [Final Checklist](#final-checklist)

## Environment Setup ✅

### 1.1 Install Python and Create a Virtual Environment ✅

- [x] Install Python 3.8+ on your machine (Completed: 2025-02-03)
- [x] Create a virtual environment by running:
  ```bash
  python3 -m venv env
  ```
- [x] Activate the virtual environment:
  ```bash
  # On Windows:
  .\env\Scripts\activate
  
  # On macOS/Linux:
  source env/bin/activate
  ```

### 1.2 Install Required Packages ✅

- [x] Create a file named "requirements.txt" with the following lines:
  ```
  openai==1.3.0
  pinecone-client==2.2.4
  faiss-cpu==1.7.4
  pandas==2.1.4
  numpy==1.26.2
  requests==2.31.0
  tqdm==4.66.1
  python-dotenv==1.0.0
  ```
- [x] Install the dependencies by running:
  ```bash
  pip install -r requirements.txt
  ```
- [x] Verify the installation with:
  ```bash
  pip list
  ```

## Project Structure Setup ✅

### 2.1 Create the Directory Structure ✅

- [x] Create the following structure:
  ```
  project/
  ├── data/
  │   └── sample_restaurant_data.csv
  ├── src/
  │   ├── ingestion.py
  │   ├── chunking.py
  │   ├── embedding.py
  │   ├── vector_db.py
  │   ├── query.py
  │   └── main.py
  ├── requirements.txt
  └── README.md
  ```

### 2.2 Initialize Git Repository ✅

- [x] Initialize Git in your project folder:
  ```bash
  git init
  ```
- [x] Create a .gitignore file to exclude your virtual environment folder and other temporary files.

## Data Ingestion Pipeline ✅

### 3.1 Read the CSV File ✅

- [x] In "src/ingestion.py", write code to load the CSV file using Pandas:
  ```python
  import pandas as pd

  def load_csv(file_path):
      return pd.read_csv(file_path)

  if __name__ == "__main__":
      df = load_csv('../data/sample_restaurant_data.csv')
      print(df.head())
  ```
- [x] Test by running:
  ```bash
  python src/ingestion.py
  ```

### 3.2 Fetch Unstructured Data (Optional) ✅

- [x] In "src/ingestion.py", add a function to fetch data from an external source:
  ```python
  import requests

  def fetch_wikipedia_article(title):
      url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
      response = requests.get(url)
      if response.status_code == 200:
          return response.json().get("extract", "")
      return ""
  ```
- [x] Test the function with a sample article title (Completed: Successfully fetched and enriched data with cuisine descriptions)

## Text Chunking and Embedding Generation ✅

### 4.1 Implement Text Chunking ✅

- [x] In "src/chunking.py", write functions to split text into manageable chunks:
  ```python
  @dataclass
  class TextChunk:
      text: str
      metadata: Dict[str, Any]
      token_count: int

  def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
      # Implementation handles:
      # - Sentence boundaries
      # - Long sentence splitting
      # - Token count estimation
      # - Metadata preservation
      pass

  def create_restaurant_chunks(restaurant_data: Dict[str, Any]) -> List[TextChunk]:
      # Creates chunks for restaurant data with metadata
      pass

  def get_ingredient_chunks(ingredients: List[str]) -> List[TextChunk]:
      # Creates chunks for ingredient lists
      pass
  ```
- [x] Test the chunking functions with sample text (Completed: Successfully processed 52,696 records into 10,716 chunks)

### 4.2 Generate Embeddings Using OpenAI ✅

- [x] In "src/embedding.py", implement a function to generate embeddings:
  ```python
  def get_embedding(text, model="text-embedding-ada-002"):
      response = client.embeddings.create(
          input=[text],
          model=model
      )
      return response.data[0].embedding
  ```
- [x] Test the embedding function with sample text snippets (Completed: Successfully generated embeddings for restaurant data chunks)
- [x] Implement batch processing for multiple chunks
- [x] Add save/load functionality for embeddings
- [x] Add proper error handling and retries
- [x] Set up secure API key management

## Storing Embeddings in the Vector Database ✅

### 5.1 Set Up Pinecone (Using Free Tier) ✅

- [x] Sign up for Pinecone and obtain your API key
- [x] In "src/vector_db.py", write functions to initialize and interact with Pinecone:
  ```python
  def init_pinecone():
      pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
      return pc.Index(INDEX_NAME)

  def upsert_embeddings(index, embedded_chunks):
      # Prepare vectors with IDs and metadata
      vectors = []
      for i, chunk in enumerate(embedded_chunks):
          vectors.append({
              'id': f"chunk_{i}",
              'values': chunk.embedding,
              'metadata': chunk.metadata
          })
      
      # Upsert in batches
      batch_size = 100
      for i in range(0, len(vectors), batch_size):
          batch = vectors[i:i + batch_size]
          index.upsert(vectors=batch)
  ```
- [x] Test the connection and basic operations (Completed: Successfully connected and verified index)
- [x] Implement batch upserting for efficiency (Completed: Implemented with batch size of 100)
- [x] Add error handling and retries (Completed: Added retry logic with max 3 attempts)
- [x] Verify data persistence (Completed: Successfully queried back upserted vectors)

## Query Processing Pipeline 🔄

### 6.1 Embed User Queries

- [ ] In "src/query.py", write code to embed user queries:
  ```python
  from embedding import get_embedding

  def embed_query(query):
      return get_embedding(query)
  ```
- [ ] Test this function with a sample query.

### 6.2 Retrieve Similar Context from the Vector DB

- [ ] In "src/query.py", add a function to query the Pinecone index:
  ```python
  def query_index(index, query_vector, top_k=5):
      result = index.query(
          vector=query_vector,
          top_k=top_k,
          include_metadata=True
      )
      return result['matches']
  ```
- [ ] Test the retrieval by embedding a sample query and checking the results.

## LLM Integration and Prompt Engineering

### 7.1 Construct the Prompt

- [ ] In "src/main.py", write a function to construct the prompt:
  ```python
  def construct_prompt(query, context_snippets):
      context_text = "\n".join(
          [f"{i+1}. {snippet['metadata']}" for i, snippet in enumerate(context_snippets)]
      )
      prompt = (
          "SYSTEM: You are an assistant for restaurant information. Use the provided data to answer questions and include source references.\n"
          f"USER QUESTION: {query}\n\n"
          "RELEVANT CONTEXT:\n"
          f"{context_text}\n\n"
          "INSTRUCTIONS: Answer the question using ONLY the above context. If the context does not contain the answer, respond with 'I don't know.'"
      )
      return prompt
  ```
- [ ] Test the prompt construction with sample data.

### 7.2 Integrate with OpenAI GPT-3.5-Turbo

- [ ] In "src/main.py", write a function to call GPT-3.5-Turbo:
  ```python
  import openai

  def generate_response(prompt, model="gpt-3.5-turbo"):
      response = openai.ChatCompletion.create(
          model=model,
          messages=[{"role": "system", "content": prompt}]
      )
      return response.choices[0].message.content

  if __name__ == "__main__":
      # Example test with a dummy prompt
      test_prompt = construct_prompt(
          "What is a popular Italian restaurant?",
          [{"metadata": "Restaurant ABC offers authentic Italian cuisine."}]
      )
      print(generate_response(test_prompt))
  ```
- [ ] Test the integration to ensure a valid response from GPT-3.5-Turbo.

## Testing and Debugging

- [ ] Run end-to-end tests:
  - Load and ingest the CSV data
  - Generate embeddings and upsert them into Pinecone
  - Embed a test query and retrieve similar context
  - Construct the prompt and generate a response
- [ ] Debug issues by checking console outputs and logs
- [ ] Refine text chunking and prompt construction based on test feedback

## Deployment

### 9.1 Prepare for Deployment

- [x] Secure API keys (store them in environment variables or a secure configuration file)
- [x] Update README with clear instructions on running the project
- [ ] (Optional) Containerize the application with Docker

### 9.2 Choose a Deployment Option

- [ ] Deploy on a cloud provider (use a small VM or a serverless platform)
- [ ] Monitor usage and cost, especially for OpenAI API calls and Pinecone usage

## Final Checklist

- [x] Environment setup completed (Python installed, virtual environment created, dependencies installed)
- [x] Project structure created with all required directories and files
- [x] CSV data is successfully loaded using the ingestion pipeline
- [x] External data fetching functions are implemented and tested
- [x] Text chunking function is implemented and returns correct chunks
- [x] Embedding generation function works correctly using OpenAI's API
- [x] Pinecone index (or your chosen vector DB) is initialized and tested
- [x] Data is successfully upserted into the vector database
- [ ] Query embedding and retrieval functions are working as expected
- [ ] Prompt construction correctly integrates user queries and retrieved context
- [ ] GPT-3.5-Turbo integration returns a valid response
- [ ] End-to-end tests pass without errors
- [ ] Deployment instructions are documented and ready for production


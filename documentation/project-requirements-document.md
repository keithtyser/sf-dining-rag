# Project Requirements Document: Conversational AI Bot for Restaurant Data (RAG-Based)

## 1. Project Overview

This document outlines the requirements for a conversational AI bot that answers questions about restaurants, menus, and ingredients by blending structured internal data with unstructured external sources. The solution leverages a Retrieval-Augmented Generation (RAG) pipeline to provide context-driven, factually accurate answers using OpenAI’s GPT-3.5-Turbo.

---

## 2. Objectives

- **Answer Diverse Queries:** Handle ingredient-based discovery, trending insights, historical/cultural context, comparative analysis, and innovation/trend queries.
- **Data Integration:** Combine proprietary structured data (CSV restaurant data) with unstructured external data (Wikipedia articles, news, blogs).
- **Cost Efficiency:** Build a Minimum Viable Product (MVP) using low-cost, scalable components.
- **Factual Consistency:** Ensure responses are grounded in retrieved context with proper source references.
- **Future Scalability:** Design a modular system that can be extended with incremental indexing, caching, and real-time data ingestion as needed.

---

## 3. Scope

- **Data Ingestion & Indexing:**  
  - Parse and process a CSV file containing restaurant data.
  - Retrieve and ingest external unstructured data.
  - Perform text chunking, generate embeddings, and store them in a vector database.

- **Retrieval Pipeline & Query Processing:**  
  - Embed user queries and perform similarity search against the indexed data.
  - Retrieve top context chunks to guide answer generation.

- **LLM Integration:**  
  - Integrate with OpenAI’s GPT-3.5-Turbo.
  - Engineer prompts that incorporate retrieved context to generate factual responses.

- **System Scalability & Cost Control:**  
  - Design for incremental updates, efficient caching, and modular component swapping.
  - Utilize free tiers or self-hosted open-source solutions to minimize costs.

---

## 4. Functional Requirements

### 4.1 Data Ingestion & Indexing

- **Structured Data Ingestion:**
  - **Input:** CSV file with columns such as `restaurant_name`, `menu_category`, `item_id`, `menu_item`, `menu_description`, `ingredient_name`, `confidence`.
  - **Process:**
    - Parse CSV rows.
    - Convert each row into a descriptive text snippet (e.g., "Restaurant ABC offers Italian cuisine with signature dish X.").
    - Apply text chunking (ideal size: 300–500 tokens) to handle long text fields.
  
- **Unstructured Data Ingestion:**
  - **Sources:** Wikipedia, news articles, food blogs.
  - **Process:**
    - Retrieve text via APIs or scraping.
    - Clean and chunk documents into coherent pieces based on natural boundaries (paragraphs or sections).

- **Embedding Generation:**
  - Use an embedding model (recommended: OpenAI Ada-002) to convert text chunks into vector representations.
  - Optionally consider open-source alternatives (e.g., SentenceTransformers) if cost demands it.

- **Indexing:**
  - **Vector Database Options:**  
    - **Weaviate:** Self-hosted (or cloud-managed) for flexible, low-cost scaling.
    - **Pinecone:** Managed service with a free tier for low-volume data.
    - **FAISS:** Open-source library for in-process vector search.
  - **Process:**
    - Store embeddings along with metadata (e.g., source, restaurant name, record ID).
    - Batch upsert embeddings to minimize API overhead.

### 4.2 Retrieval Pipeline & Query Processing

- **Query Embedding:**
  - Convert user queries into vector embeddings using the same embedding model.

- **Similarity Search:**
  - Perform a vector search (e.g., cosine similarity) to retrieve the top *k* (e.g., 3–5) most relevant text chunks.
  - Optionally apply metadata filters (e.g., filter by location or cuisine).

- **Prompt Engineering:**
  - Construct a prompt that includes:
    - A system message with clear instructions.
    - The user’s query.
    - Retrieved context snippets (with source references).
    - A directive for the LLM to answer using only the provided context (with a fallback message if necessary).
  
- **Fallback Handling:**
  - If retrieved context is insufficient, instruct GPT-3.5-Turbo to respond with "I don't know" or a similar fallback message.

- **Prompt Structure Example:**

    > SYSTEM: You are an assistant for restaurant information. Use the provided data to answer questions and include source references.
    >
    > USER QUESTION: *<User's question here>*
    >
    > RELEVANT CONTEXT:
    >  1. *<Context snippet 1>*
    >  2. *<Context snippet 2>*
    >  3. *<Context snippet 3>*
    >
    > INSTRUCTIONS: Answer the question using ONLY the above context. If the context does not contain the answer, respond with "I don’t know."

### 4.3 LLM Integration

- **Model:** OpenAI GPT-3.5-Turbo.
- **Output:**
  - The LLM generates a response that is concise, factually correct, and includes source citations where applicable.

### 4.4 Scalability & Future-Proofing

- **Incremental Indexing:**  
  - Allow new data (structured or unstructured) to be added without re-indexing the entire dataset.
- **Caching Strategies:**  
  - Cache embeddings to avoid redundant computation.
  - Implement query result caching for frequently asked questions.
- **Modularity:**  
  - Use frameworks like LangChain or LlamaIndex for easier future integration and component swapping.
- **Resource Optimization:**  
  - Monitor usage to ensure that API calls and data processing remain cost-effective.
  - Plan to scale the vector database and processing components only when usage demands it.

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **Latency:**  
  - Ensure real-time query processing with sub-100ms vector search times.
- **Batch Efficiency:**  
  - Optimize batch processing during data ingestion to reduce downtime.

### 5.2 Cost Efficiency
- Utilize free tiers (e.g., Pinecone free tier, self-hosted Weaviate, FAISS) and open-source components.
- Optimize prompt lengths and query frequency to keep OpenAI API costs minimal.

### 5.3 Maintainability & Extensibility
- Modular code architecture separating ingestion, indexing, retrieval, and response generation.
- Clear documentation for all modules and API integrations.
- Easy swapping of components (e.g., vector DB or embedding model) with minimal code changes.

### 5.4 Security & Privacy
- Encrypt data in transit and at rest.
- Disable data logging for API calls where possible (OpenAI settings).
- Secure vector database endpoints if self-hosted (authentication, HTTPS).
- Ensure compliance with data privacy regulations (e.g., GDPR) as applicable.

---

## 6. Technical Architecture & Stack

### 6.1 Components

- **Data Sources:**
  - **Structured:** CSV file with restaurant data.
  - **Unstructured:** Wikipedia articles, news, and blog posts.

- **Data Ingestion Pipeline:**
  - CSV parsers and web scrapers.
  - Text chunking and cleaning modules.

- **Embedding Generation:**
  - Recommended: OpenAI Ada-002 embeddings.
  - Alternative: Open-source models (e.g., SentenceTransformers).

- **Vector Database:**
  - **Primary Options:**  
    - **Weaviate** (self-hosted/cloud-managed) for low-cost, scalable storage.
    - **Pinecone** (managed) for a hassle-free setup.
    - **FAISS** for a free, in-process solution.
  
- **LLM Integration:**
  - OpenAI GPT-3.5-Turbo for natural language understanding and generation.

- **Orchestration & Frameworks:**
  - Optionally, use LangChain or LlamaIndex to facilitate prompt engineering, chaining, and caching.

### 6.2 Data Flow Overview

1. **Data Ingestion:**  
   - Parse and process the CSV file and external sources.
   - Clean, chunk, and generate embeddings.
   - Batch upsert the embeddings into the chosen vector database.

2. **Query Processing:**  
   - Convert the user query into an embedding.
   - Perform similarity search in the vector database to retrieve relevant context.
   - Construct a prompt using the retrieved context and user query.

3. **Response Generation:**  
   - Send the constructed prompt to GPT-3.5-Turbo.
   - Receive and display the final answer with appropriate source references.

---

## 7. Example Code Snippets

### 7.1 Data Ingestion Pseudocode
```python
import csv
from your_embedding_library import get_embedding
from your_vector_db_client import VectorDBClient, generate_id

# Initialize vector database client and embedding model
vector_db = VectorDBClient(api_key="YOUR_API_KEY")
embedding_model = get_embedding(model="openai-ada-002")

def chunk_text(text, max_tokens=500):
    # Implement text chunking logic (e.g., split by paragraphs, sentences)
    return [text[i:i+max_tokens] for i in range(0, len(text), max_tokens)]

with open('restaurant_data.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Construct descriptive text for each row
        doc_text = f"{row['restaurant_name']} offers {row['menu_item']} in category {row['menu_category']}. Details: {row['menu_description']}"
        text_chunks = chunk_text(doc_text)
        for chunk in text_chunks:
            vector = embedding_model.embed(chunk)
            metadata = {
                "restaurant_name": row['restaurant_name'],
                "item_id": row['item_id'],
                "source": "proprietary CSV"
            }
            vector_db.upsert(id=generate_id(), vector=vector, metadata=metadata)
```

### 7.2 Query Processing and Prompt Construction

def construct_prompt(query, context_chunks):
    context_text = "\n".join([f"{i+1}. {chunk}" for i, chunk in enumerate(context_chunks)])
    prompt = (
        "SYSTEM: You are an assistant for restaurant information. Use the provided data to answer questions and include source references.\n"
        f"USER QUESTION: {query}\n\n"
        "RELEVANT CONTEXT:\n"
        f"{context_text}\n\n"
        "INSTRUCTIONS: Answer the question using ONLY the above context. If the context does not contain the answer, respond with 'I don’t know.'"
    )
    return prompt

# Example usage:
query = "Which restaurants in Los Angeles serve gluten-free pizza?"
context_chunks = [
    "Restaurant XYZ offers gluten-free pizza in downtown LA. (Source: proprietary CSV, ID: 24932146)",
    "Restaurant ABC in Los Angeles has a dedicated gluten-free menu. (Source: external blog, URL: https://example.com)"
]

prompt = construct_prompt(query, context_chunks)
print(prompt)

8. Deliverables
Technical Design Document: This requirements document.
Working Prototype: Code samples, notebooks, and a minimal API/CLI demonstration.
Sample Conversations: Demonstrative Q&A sessions showing context retrieval and proper source references.
Deployment Plan: Guidelines for deploying the MVP on a cost-effective cloud environment or self-hosted solution.

9. Timeline & Milestones
Weeks 1-2:
Finalize requirements and set up the data ingestion pipeline.
Weeks 3-4:
Implement vector database indexing and retrieval components.
Week 5:
Integrate OpenAI GPT-3.5-Turbo with prompt engineering; perform end-to-end testing.
Week 6:
Develop a demo interface and deploy the MVP for internal evaluation.
Post-MVP:
Iterate based on user feedback and add improvements such as incremental indexing and caching.

10. References
OpenAI Ada-002 Embeddings Documentation: OpenAI API
Pinecone Vector Database: Pinecone Docs
Weaviate Vector Search: Weaviate Documentation
FAISS Library: FAISS GitHub
LangChain Framework: LangChain Docs
Haystack for RAG: Haystack Documentation

11. Summary
This document provides a comprehensive, modular set of requirements to build a low-cost, scalable RAG-based conversational AI bot for restaurant data. The proposed design integrates both structured and unstructured data, leverages efficient text processing and vector search, and uses OpenAI’s GPT-3.5-Turbo for generating responses anchored in retrieved context. This approach minimizes costs while ensuring future scalability and maintainability.
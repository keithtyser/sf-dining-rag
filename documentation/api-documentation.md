# Restaurant Chat API Documentation

## Overview

This document provides comprehensive documentation for the Restaurant Chat API, which offers endpoints for restaurant information retrieval and natural language interactions about restaurants, menus, and related topics.

## Base URL

```
/api/v1
```

## Authentication

Currently, the API does not require authentication. Rate limiting is applied to prevent abuse.

## Rate Limits

The API implements rate limiting to ensure fair usage:

- Chat endpoints: 30 requests per minute
- Conversation management: 60 requests per minute
- Cleanup operations: 10 requests per minute

When rate limits are exceeded, the API returns a 429 status code with details about retry timing.

## Endpoints

### Health Check

```http
GET /health
```

Check the API's health status.

**Response Example:**
```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

### Chat Completion

```http
POST /chat
```

Generate an AI response based on user query and conversation context.

**Request Body:**
```json
{
    "query": "What are the best Italian restaurants?",
    "conversation_id": "abc123",  // Optional
    "context_window_size": 5,     // Optional, default: 5
    "metadata": {                 // Optional
        "user_id": "123",
        "session_id": "abc"
    }
}
```

**Response Example:**
```json
{
    "response": "Based on our data, Bella Italia on Main Street is highly rated...",
    "conversation_id": "abc123",
    "metadata": {
        "response_time": 0.8,
        "tokens_used": 150,
        "context_chunks": 3
    }
}
```

**Rate Limit:**
- 30 requests per minute
- Retry-After: 30 seconds when limit exceeded

### Get Recent Conversations

```http
GET /conversations/recent
```

Retrieve recent conversation history.

**Query Parameters:**
- `limit` (optional): Maximum number of conversations to return (default: 10, max: 50)

**Response Example:**
```json
[
    {
        "conversation_id": "abc123",
        "messages": [
            {
                "role": "user",
                "content": "What are the best Italian restaurants?",
                "timestamp": 1634567890.123
            },
            {
                "role": "assistant",
                "content": "Based on our data...",
                "timestamp": 1634567891.456
            }
        ],
        "metadata": {
            "created_at": 1634567890.123,
            "last_updated": 1634567891.456
        }
    }
]
```

### Get Conversation by ID

```http
GET /chat/{conversation_id}
```

Retrieve a specific conversation by ID.

**Response Example:**
```json
{
    "conversation_id": "abc123",
    "messages": [...],
    "metadata": {...}
}
```

### Clean Up Old Conversations

```http
POST /chat/cleanup
```

Clean up conversations older than specified days.

**Request Body:**
```json
{
    "days_old": 30
}
```

**Response Example:**
```json
{
    "status": "success",
    "message": "Old conversations cleaned up"
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

- 400: Bad Request
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

**Error Response Example:**
```json
{
    "error": "rate_limit_exceeded",
    "message": "Too many requests to chat endpoint. Please try again later.",
    "endpoint_type": "chat",
    "retry_after": 30
}
```

## Performance Benchmarks

Based on recent testing:

- Average response time: 200-500ms
- 95th percentile response time: <1s
- Rate limit capacity: 30 requests/minute for chat endpoints
- Concurrent users supported: Up to 100

## Best Practices

1. **Conversation Management**
   - Store conversation IDs for continued interactions
   - Use context_window_size appropriately (5-10 messages)
   - Clean up old conversations regularly

2. **Rate Limiting**
   - Implement exponential backoff when limits are hit
   - Cache responses when appropriate
   - Monitor rate limit headers

3. **Error Handling**
   - Always check response status codes
   - Implement proper error handling
   - Log and monitor error responses

## Examples

### Python Example

```python
import requests

BASE_URL = "http://your-api-url/api/v1"

def chat_with_restaurant_api(query, conversation_id=None):
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "query": query,
            "conversation_id": conversation_id,
            "context_window_size": 5
        }
    )
    
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        print(f"Rate limit exceeded. Try again in {retry_after} seconds")
        return None
        
    if response.status_code == 200:
        return response.json()
    
    print(f"Error: {response.status_code}")
    return None

# Example usage
response = chat_with_restaurant_api("What are the best Italian restaurants?")
if response:
    print(response["response"])
    conversation_id = response["conversation_id"]
    
    # Continue conversation
    follow_up = chat_with_restaurant_api(
        "What's their price range?",
        conversation_id=conversation_id
    )
```

### JavaScript Example

```javascript
const BASE_URL = 'http://your-api-url/api/v1';

async function chatWithRestaurantApi(query, conversationId = null) {
    try {
        const response = await fetch(`${BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                conversation_id: conversationId,
                context_window_size: 5
            })
        });
        
        if (response.status === 429) {
            const retryAfter = response.headers.get('Retry-After');
            console.log(`Rate limit exceeded. Try again in ${retryAfter} seconds`);
            return null;
        }
        
        if (response.ok) {
            return await response.json();
        }
        
        console.error(`Error: ${response.status}`);
        return null;
        
    } catch (error) {
        console.error('API call failed:', error);
        return null;
    }
}

// Example usage
async function example() {
    const response = await chatWithRestaurantApi('What are the best Italian restaurants?');
    if (response) {
        console.log(response.response);
        const conversationId = response.conversation_id;
        
        // Continue conversation
        const followUp = await chatWithRestaurantApi(
            "What's their price range?",
            conversationId
        );
    }
}
```

## Support

For API support or to report issues, please contact the development team or create an issue in the project repository.

## Changelog

### Version 1.0.0
- Initial API release
- Basic chat functionality
- Conversation management
- Rate limiting implementation
- Error handling 
import OpenAI from 'openai';
import { NextRequest } from 'next/server';

// Available models
const MODELS = {
  'chatgpt-4o-latest': 'ChatGPT-4o Latest',
  'o1-mini': 'o1-mini'
} as const;

// Runtime configuration
export const runtime = 'nodejs';
export const revalidate = 0;

// Define the type for our context chunk
interface ContextChunk {
  id: string;
  text: string;
  tokens: number;
  metadata: {
    source: string;
    source_type: 'restaurant' | 'news' | 'wikipedia' | string;
    title: string;
    text?: string;
    restaurant: string;
    category: string;
    item_name: string;
    description: string;
    ingredients: string[];
    categories: string[];
    keywords: string[];
    rating: number;
    review_count: number;
    price: string;
    address: string;
    position: number;
    similarity: number;
    tokens: number;
    publish_date?: string;
    summary?: string;
  };
}

// Add these type definitions after the ContextChunk interface
interface SanitizedChunk extends ContextChunk {
  metadata: ContextChunk['metadata'] & {
    text?: string;
    title?: string;
    description?: string;
    summary?: string;
  };
}

// Add this helper function after the interface definitions
async function rewriteQueryWithContext(openai: OpenAI, messages: any[]): Promise<string> {
  try {
    const completion = await openai.chat.completions.create({
      model: 'chatgpt-4o-latest',
      messages: [
        {
          role: 'system',
          content: `You are a query optimization assistant for a restaurant search system. Your task is to extract only the essential search keywords from user queries, maintaining context from the conversation.

Guidelines:
1. Focus ONLY on:
   - Cuisine types (italian, chinese, etc.)
   - Dish types (pizza, sushi, etc.)
   - Key attributes (casual, fancy, outdoor seating, etc.)
   - Price indicators (cheap, expensive, etc.)
   - Specific requirements (vegetarian, gluten-free, etc.)

2. Rules:
   - Return ONLY the essential keywords
   - Do not include "San Francisco" or "SF" (all restaurants are in SF)
   - Keep it minimal (1-3 keywords)
   - Use lowercase only
   - For follow-up queries, maintain the relevant context (especially cuisine type)
   - If a query mentions a non-SF location, extract only the cuisine/requirements

3. Context Handling:
   - If user confirms or asks for recommendations after mentioning a cuisine, keep that cuisine
   - If user asks about a different attribute, combine it with previous cuisine
   - If user completely changes topic, use new keywords only

Examples:
User: "I want some good Italian food"
Return: "italian"

User: "What about something more casual?"
Return: "italian casual"

User: "What's the best Chinese place in San Diego?"
Return: "chinese"

User: "Yes, give me San Francisco recommendations"
Return: "chinese"

User: "Show me places with outdoor seating"
Return: "outdoor seating"

User: "Looking for fancy sushi places in the city"
Return: "sushi fancy"`
        },
        ...messages.slice(0, -1),
        {
          role: 'user',
          content: `Based on this conversation history, extract the optimal search keywords from: "${messages[messages.length - 1].content}"`
        }
      ]
    });

    const rewrittenQuery = completion.choices[0]?.message?.content || messages[messages.length - 1].content;
    console.log('\n=== Query Information ===');
    console.log('Original query:', messages[messages.length - 1].content);
    console.log('Optimized query:', rewrittenQuery);
    console.log('========================\n');
    return rewrittenQuery;
  } catch (error) {
    console.error('Error rewriting query:', error);
    return messages[messages.length - 1].content;
  }
}

async function queryPineconeIndex(queryEmbedding: number[], indexName: string, pineconeApiKey: string, pineconeHost: string): Promise<any> {
  try {
    // Construct the URL - try both direct host and parsed format
    let pineconeUrl;
    if (pineconeHost.includes(indexName)) {
      // If the host already includes the index name, use it directly
      pineconeUrl = `https://${pineconeHost}/query`;
    } else {
      // Otherwise, try to parse and construct the URL
      try {
        const [projectId, , envId] = pineconeHost.split('.');
        const baseProjectId = projectId.split('-').slice(-1)[0];
        pineconeUrl = `https://${indexName}-${baseProjectId}.svc.${envId}.pinecone.io/query`;
      } catch (e) {
        // If parsing fails, try using the host directly
        pineconeUrl = `https://${pineconeHost}/query`;
      }
    }
    
    console.log(`Attempting to query Pinecone index ${indexName} at ${pineconeUrl}`);
    
    const pineconeResponse = await fetch(pineconeUrl, {
      method: 'POST',
      headers: {
        'Api-Key': pineconeApiKey,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        vector: queryEmbedding,
        topK: 20,
        includeMetadata: true,
        includeValues: false
      }),
    });

    if (!pineconeResponse.ok) {
      const errorText = await pineconeResponse.text();
      console.error(`Pinecone query failed for index ${indexName}:`, {
        status: pineconeResponse.status,
        statusText: pineconeResponse.statusText,
        error: errorText,
        url: pineconeUrl
      });
      throw new Error(`Pinecone query failed: ${pineconeResponse.status} ${pineconeResponse.statusText}. ${errorText}`);
    }

    const result = await pineconeResponse.json();
    console.log(`Successfully queried index ${indexName}. Found ${result.matches?.length || 0} matches.`);
    return result;
  } catch (error) {
    console.error(`Error querying Pinecone index ${indexName}:`, {
      error: error instanceof Error ? error.message : String(error),
      host: pineconeHost,
      indexName
    });
    return { matches: [] };
  }
}

// Add these helper functions at the top level
function sanitizeText(text: string, preserveMarkdown: boolean = false): string {
  if (!text) return '';
  
  // If we need to preserve markdown, handle special cases
  if (preserveMarkdown) {
    return text
      .replace(/\\/g, '\\\\')  // Escape backslashes first
      .replace(/\r/g, '')      // Remove carriage returns
      .replace(/\t/g, '  ')    // Replace tabs with spaces
      .replace(/\f/g, '')      // Remove form feeds
      .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, '') // Remove control characters except \n
      .replace(/"/g, '\\"');   // Escape quotes
  }
  
  // Otherwise use the more aggressive sanitization
  return text
    .replace(/\\/g, '\\\\')    // Escape backslashes first
    .replace(/\n/g, '\\n')     // Replace newlines with \n
    .replace(/\r/g, '\\r')     // Replace carriage returns
    .replace(/\t/g, '\\t')     // Replace tabs
    .replace(/"/g, '\\"')      // Escape quotes
    .replace(/\f/g, '\\f')     // Replace form feeds
    .replace(/[\u0000-\u001F\u007F-\u009F]/g, ''); // Remove control characters
}

function sanitizeMetadata(metadata: any): any {
  if (!metadata) return {};
  const sanitized: any = {};
  for (const [key, value] of Object.entries(metadata)) {
    if (typeof value === 'string') {
      sanitized[key] = sanitizeText(value);
    } else if (Array.isArray(value)) {
      sanitized[key] = value.map(item => 
        typeof item === 'string' ? sanitizeText(item) : item
      );
    } else {
      sanitized[key] = value;
    }
  }
  return sanitized;
}

function sanitizeChunk(chunk: any): any {
  return {
    id: chunk.id,
    text: sanitizeText(chunk.text),
    tokens: chunk.tokens,
    metadata: sanitizeMetadata(chunk.metadata)
  };
}

function formatSSEMessage(data: any): string {
  try {
    const jsonString = JSON.stringify(data);
    // Ensure proper SSE format with data: prefix and double newline
    return `data: ${jsonString}\n\n`;
  } catch (error) {
    console.error('Error formatting SSE message:', error);
    return '';
  }
}

export async function POST(req: NextRequest) {
  try {
    // Validate environment variables
    const apiKey = process.env.OPENAI_API_KEY;
    const pineconeApiKey = process.env.PINECONE_API_KEY;
    const pineconeHost = process.env.PINECONE_HOST;

    if (!apiKey) throw new Error('OPENAI_API_KEY environment variable is not set');
    if (!pineconeApiKey) throw new Error('PINECONE_API_KEY environment variable is not set');
    if (!pineconeHost) throw new Error('PINECONE_HOST environment variable is not set');

    const openai = new OpenAI({ apiKey: apiKey });

    const { 
      messages, 
      model = 'chatgpt-4o-latest',
      temperature = 0.7,
      maxTokens = 2000,
      topP = 1,
      presencePenalty = 0,
      frequencyPenalty = 0,
    } = await req.json();

    // Validate model
    if (!Object.keys(MODELS).includes(model)) {
      throw new Error(`Invalid model. Must be one of: ${Object.keys(MODELS).join(', ')}`);
    }

    const latestUserMessage = messages.filter((msg: any) => msg.role === 'user').pop();
    if (!latestUserMessage) throw new Error('No user message found');

    const rewrittenQuery = await rewriteQueryWithContext(openai, messages);
    const embeddingResponse = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: rewrittenQuery,
    });
    const queryEmbedding = embeddingResponse.data[0].embedding;

    // Query each index separately
    const [restaurantResults, wikipediaResults, newsResults] = await Promise.all([
      queryPineconeIndex(queryEmbedding, 'restaurant-chatbot', pineconeApiKey, pineconeHost),
      queryPineconeIndex(queryEmbedding, 'wikipedia-chunks', pineconeApiKey, pineconeHost),
      queryPineconeIndex(queryEmbedding, 'news-chunks', pineconeApiKey, pineconeHost)
    ]);

    // Process chunks from each source
    const restaurantChunks = restaurantResults.matches.map((match: any, index: number) => {
      const tokenCount = match.metadata?.tokens || Math.ceil((match.metadata?.text || '').length / 4);
      const uniqueId = `restaurant_${match.id}_${index}`;
      return {
        id: uniqueId,
        text: match.metadata?.text || '',
        tokens: tokenCount,
        metadata: {
          ...match.metadata,
          position: index + 1,
          similarity: match.score || 0,
          source_type: 'restaurant',
          source: 'restaurant'
        }
      };
    });

    const wikipediaChunks = wikipediaResults.matches.map((match: any, index: number) => {
      const tokenCount = match.metadata?.tokens || Math.ceil((match.metadata?.text || '').length / 4);
      const uniqueId = `wikipedia_${match.id}_${index}`;
      return {
        id: uniqueId,
        text: match.metadata?.text || '',
        tokens: tokenCount,
        metadata: {
          ...match.metadata,
          position: index + 1,
          similarity: match.score || 0,
          source_type: 'wikipedia',
          source: 'wikipedia'
        }
      };
    });

    const newsChunks = newsResults.matches.map((match: any, index: number) => {
      const tokenCount = match.metadata?.tokens || Math.ceil((match.metadata?.text || '').length / 4);
      const uniqueId = `news_${match.id}_${index}`;
      return {
        id: uniqueId,
        text: match.metadata?.text || '',
        tokens: tokenCount,
        metadata: {
          ...match.metadata,
          position: index + 1,
          similarity: match.score || 0,
          source_type: 'news',
          source: 'news'
        }
      };
    });

    // Format chunks by source type
    const formatChunks = (chunks: any[], sourceType: string) => {
      if (chunks.length === 0) return "NO RELEVANT CONTEXT FOUND";
      
      return chunks.map((chunk: any, i: number) => {
        const metadata = chunk.metadata;
        let output = `╭──────────── ${sourceType.toUpperCase()} CONTEXT ${i + 1} ────────────\n`;
        output += `│ Source: ${metadata.source || sourceType}\n`;
        output += `│ Relevance: ${(metadata.similarity * 100).toFixed(0)}%\n`;

        switch(sourceType) {
          case 'restaurant':
            if (metadata.restaurant_name) {
              output += `│ Restaurant: ${metadata.restaurant_name}\n`;
              if (metadata.rating) output += `│ Rating: ${metadata.rating} stars${metadata.review_count ? ` (${metadata.review_count} reviews)` : ''}\n`;
              if (metadata.price) output += `│ Price: ${metadata.price}\n`;
              if (metadata.address1) output += `│ Address: ${metadata.address1}\n`;
              if (metadata.categories) output += `│ Categories: ${typeof metadata.categories === 'string' ? metadata.categories : metadata.categories.join(', ')}\n`;
            }
            break;
            
          case 'wikipedia':
            output += `│ Title: ${metadata.title || 'N/A'}\n`;
            if (metadata.summary) output += `│ Summary: ${metadata.summary}\n`;
            if (metadata.url) output += `│ URL: ${metadata.url}\n`;
            break;
            
          case 'news':
            output += `│ Title: ${metadata.title || 'N/A'}\n`;
            if (metadata.publish_date) output += `│ Published: ${new Date(metadata.publish_date).toLocaleDateString()}\n`;
            if (metadata.url) output += `│ URL: ${metadata.url}\n`;
            break;
        }

        if (chunk.text) {
          const previewText = chunk.text.length > 150 ? chunk.text.substring(0, 150) + '...' : chunk.text;
          output += `│ Preview: ${previewText.replace(/\n/g, ' ')}\n`;
        }
        
        output += `╰${'─'.repeat(50)}`;
        return output;
      }).join('\n\n');
    };

    const finalMessages = [
      {
        role: "system" as const,
        content: `You are an expert assistant for SF Dining Guide, specializing in San Francisco restaurants and dining experiences. You have access to three types of information:

1. RESTAURANT DATA: Detailed information about San Francisco restaurants, including menus, ratings, and locations
2. WIKIPEDIA CONTEXT: Background information about cuisines, cooking techniques, and food culture
3. NEWS ARTICLES: Recent updates about the San Francisco dining scene

GUIDELINES:

1. REASONING AND ACCURACY:
- Analyze all available context types (restaurant, Wikipedia, news) internally
- Prioritize restaurant data for specific dining recommendations
- Use Wikipedia for background/educational content
- Use news for recent developments and current trends
- Form clear, factual conclusions based on the evidence
- When ranking restaurants, consider factors like ratings, reviews, and relevance

2. SOURCE ATTRIBUTION:
- Only cite sources that you actually use in your response
- Reference specific sources with their type and relevance score
- Format source references based on type:
  * Restaurants: [Restaurant Name, SF | Score: XX%]
  * Wikipedia: [Wikipedia: Title | Score: XX%]
  * News: [News: Source - Date | Score: XX%]
- If you don't use a particular type of source, don't cite it

3. HANDLING DATA LIMITATIONS:
- If context is missing crucial information, explicitly state what's missing
- When data is conflicting, explain the discrepancy and your reasoning
- If confidence is low, provide appropriate disclaimers
- Note that restaurant recommendations are limited to San Francisco
- If asked about restaurants outside SF, politely explain that you can only assist with San Francisco dining options

4. RESPONSE FORMAT:
Start with a natural, direct response to the user's query, speaking as a knowledgeable San Francisco dining guide. Then include:

---
Selection Criteria: [Brief explanation of how you ranked or selected information]
Sources Used: [List only the sources you actually referenced in your response]
Confidence: [High/Medium/Low with brief explanation]
Notes: [Any disclaimers, limitations, or suggestions if needed]`
      },
      ...messages.slice(0, -1),
      {
        role: "user" as const,
        content: `USER QUERY:
${latestUserMessage.content}

RESTAURANT CONTEXT:
${formatChunks(restaurantChunks, 'restaurant')}

WIKIPEDIA CONTEXT:
${formatChunks(wikipediaChunks, 'wikipedia')}

NEWS CONTEXT:
${formatChunks(newsChunks, 'news')}`
      }
    ];

    // Log the context and final prompt
    console.log('\n=== Query Information ===');
    console.log('Original query:', latestUserMessage.content);
    console.log('Optimized query:', rewrittenQuery);
    
    console.log('\n=== Retrieved Context ===');
    console.log(`Restaurant Chunks: ${restaurantChunks.length}`);
    console.log(`Wikipedia Chunks: ${wikipediaChunks.length}`);
    console.log(`News Chunks: ${newsChunks.length}`);
    
    console.log('\n=== Final Prompt ===');
    console.log(JSON.stringify(finalMessages, null, 2));
    console.log('==================\n');

    // Create a streaming chat completion
    const completion = await openai.chat.completions.create({
      model,
      temperature,
      max_tokens: maxTokens,
      top_p: topP,
      presence_penalty: presencePenalty,
      frequency_penalty: frequencyPenalty,
      messages: finalMessages,
      stream: true,
    });

    // Set up the response stream
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        
        try {
          // Sanitize chunks before sending
          const sanitizedChunks = {
            restaurant: restaurantChunks.map(sanitizeChunk),
            wikipedia: wikipediaChunks.map(sanitizeChunk),
            news: newsChunks.map(sanitizeChunk)
          };

          // Send context data
          const contextMessage = formatSSEMessage({
            type: 'context',
            chunks: sanitizedChunks
          });
          controller.enqueue(encoder.encode(contextMessage));

          // Stream completion chunks
          for await (const chunk of completion) {
            const content = chunk.choices[0]?.delta?.content || '';
            if (content) {
              const contentMessage = formatSSEMessage({
                type: 'content',
                content: sanitizeText(content, true)  // Preserve markdown for content
              });
              controller.enqueue(encoder.encode(contentMessage));
            }
          }
          
          // Send end message
          const endMessage = formatSSEMessage({ type: 'done' });
          controller.enqueue(encoder.encode(endMessage));
          
          controller.close();
        } catch (error) {
          console.error('Streaming error:', error);
          const errorMessage = formatSSEMessage({
            type: 'error',
            error: error instanceof Error ? error.message : 'Unknown error occurred'
          });
          controller.enqueue(encoder.encode(errorMessage));
          controller.error(error);
        }
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'An error occurred during chat',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
} 
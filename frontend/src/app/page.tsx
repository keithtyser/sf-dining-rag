"use client";

import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { ContextPanel } from '@/components/chat/ContextPanel';
import type { Message } from '@/types/chat';
import { cn } from '@/lib/utils';
import { Compass, MessageSquare, Search, Sparkles } from 'lucide-react';

// Welcome message component
function WelcomeMessage({ onExampleClick }: { onExampleClick: (query: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4 py-8 animate-in fade-in-50 duration-500">
      <div className="max-w-2xl space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight sf-heading">
            Welcome to SF Dining Guide
          </h1>
          <p className="text-muted-foreground">
            Your AI-powered assistant for discovering San Francisco's vibrant dining scene
          </p>
        </div>

        {/* Features */}
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="flex flex-col items-center gap-2 p-4 rounded-lg border bg-card text-card-foreground">
            <Search className="h-6 w-6 text-[hsl(var(--sf-golden-gate))]" />
            <h3 className="font-semibold">Smart Search</h3>
            <p className="text-sm text-muted-foreground">Find restaurants by cuisine, price, or vibe</p>
          </div>
          <div className="flex flex-col items-center gap-2 p-4 rounded-lg border bg-card text-card-foreground">
            <MessageSquare className="h-6 w-6 text-[hsl(var(--sf-golden-gate))]" />
            <h3 className="font-semibold">Natural Chat</h3>
            <p className="text-sm text-muted-foreground">Ask questions in your own words</p>
          </div>
          <div className="flex flex-col items-center gap-2 p-4 rounded-lg border bg-card text-card-foreground">
            <Sparkles className="h-6 w-6 text-[hsl(var(--sf-golden-gate))]" />
            <h3 className="font-semibold">Live Updates</h3>
            <p className="text-sm text-muted-foreground">Get the latest news and openings</p>
          </div>
        </div>

        {/* Example queries */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Try asking about:</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {[
              "What are the best Italian restaurants in North Beach?",
              "Find me a romantic spot for date night",
              "Show me new restaurant openings this month",
              "Where can I find authentic dim sum?",
              "What are the top-rated sushi places?",
              "Recommend casual spots with outdoor seating"
            ].map((query, i) => (
              <button
                key={i}
                onClick={() => onExampleClick(query)}
                className="p-3 text-sm rounded-lg border bg-muted/50 hover:bg-muted/80 cursor-pointer transition-colors text-left"
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [contextChunks, setContextChunks] = useState<{
    restaurant: any[];
    wikipedia: any[];
    news: any[];
  }>({
    restaurant: [],
    wikipedia: [],
    news: []
  });
  const [isLoading, setIsLoading] = useState(false);
  const [finalPrompt, setFinalPrompt] = useState<string>('');
  const [isContextCollapsed, setIsContextCollapsed] = useState(true);

  const handleSendMessage = async (message: string) => {
    setIsLoading(true);
    
    // Add user message immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // Prepare the prompt with context and conversation history
      const prompt = {
        messages: [
          ...messages.map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          {
            role: 'user',
            content: message
          }
        ],
        model: 'chatgpt-4o-latest',
        temperature: 0.7,
        maxTokens: 2000,
        topP: 1,
        presencePenalty: 0,
        frequencyPenalty: 0,
      };

      setFinalPrompt(JSON.stringify(prompt, null, 2));

      // Use EventSource for proper SSE handling
      const eventSource = new EventSource('/api/chat/stream?' + new URLSearchParams({
        prompt: JSON.stringify(prompt)
      }));

      // Create assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Handle SSE events
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'content':
              setMessages(prev => {
                const lastMessage = prev[prev.length - 1];
                if (lastMessage.role === 'assistant') {
                  return [
                    ...prev.slice(0, -1),
                    {
                      ...lastMessage,
                      content: lastMessage.content + data.content,
                    },
                  ];
                }
                return prev;
              });
              break;

            case 'context':
              setContextChunks(data.chunks);
              break;

            case 'error':
              console.error('Stream error:', data.error);
              setMessages(prev => {
                const lastMessage = prev[prev.length - 1];
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMessage,
                    status: 'error',
                    error: data.error,
                  },
                ];
              });
              eventSource.close();
              setIsLoading(false);
              break;

            case 'done':
              eventSource.close();
              setIsLoading(false);
              break;
          }
        } catch (e) {
          console.error('Error parsing SSE data:', e);
          eventSource.close();
          setIsLoading(false);
        }
      };

      // Handle connection errors
      eventSource.onerror = (error) => {
        console.error('SSE Connection Error:', error);
        eventSource.close();
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              status: 'error',
              error: 'Connection error occurred. Please try again.',
            },
          ];
        });
        setIsLoading(false);
      };

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        return [
          ...prev.slice(0, -1),
          {
            ...lastMessage,
            status: 'error',
            error: error instanceof Error ? error.message : 'Failed to send message',
          },
        ];
      });
      setIsLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className={cn(
        "grid h-[calc(100vh-4rem)] gap-4 p-4",
        isContextCollapsed ? "grid-cols-[1fr_auto]" : "grid-cols-[3fr_1fr]"
      )}>
        <div className="relative min-w-[500px] h-full flex flex-col overflow-hidden">
          {messages.length === 0 ? (
            <>
              <div className="flex-1 overflow-y-auto">
                <WelcomeMessage onExampleClick={handleSendMessage} />
              </div>
              <div className="flex-shrink-0 p-4 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/75">
                <ChatContainer
                  messages={[]}
                  isLoading={isLoading}
                  onSendMessage={handleSendMessage}
                  finalPrompt={finalPrompt}
                  className="shadow-none border-none"
                  hideMessages
                />
              </div>
            </>
          ) : (
            <ChatContainer
              messages={messages}
              isLoading={isLoading}
              onSendMessage={handleSendMessage}
              finalPrompt={finalPrompt}
              className="h-full"
            />
          )}
        </div>
        <ContextPanel
          chunks={contextChunks}
          onChunkClick={(chunk) => {
            console.log('Chunk clicked:', chunk);
          }}
          onClearContext={() => setContextChunks({
            restaurant: [],
            wikipedia: [],
            news: []
          })}
          className={cn(
            "h-full transition-all duration-200",
            isContextCollapsed ? "w-[50px]" : "min-w-[300px]"
          )}
          isCollapsed={isContextCollapsed}
          onToggleCollapse={() => setIsContextCollapsed(!isContextCollapsed)}
        />
      </div>
    </MainLayout>
  );
}

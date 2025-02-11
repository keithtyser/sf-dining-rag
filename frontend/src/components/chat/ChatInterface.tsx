"use client";

import { useState } from 'react';
import { Send, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { ChatMessage } from './ChatMessage';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface Message {
  content: string;
  isUser: boolean;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { content: input, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Add API call here
      const response = { content: "This is a sample response." };
      setMessages(prev => [...prev, { content: response.content, isUser: false }]);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Messages Container */}
      <Card className="flex-1 overflow-hidden rounded-lg border bg-background/50 backdrop-blur-sm">
        <div className="flex h-full flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <div className="text-center space-y-4">
                  <div className="animate-float">
                    <span className="text-6xl">🍽️</span>
                  </div>
                  <div className="space-y-2">
                    <h2 className="text-2xl font-semibold text-foreground/80">
                      Welcome to SF Dining Guide!
                    </h2>
                    <p className="text-muted-foreground max-w-sm">
                      Ask me anything about San Francisco restaurants, local specialties, or dining recommendations.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <ChatMessage
                  key={index}
                  content={message.content}
                  isUser={message.isUser}
                />
              ))
            )}
            {isLoading && (
              <div className="flex items-center justify-center py-2">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            )}
          </div>

          {/* Input Form */}
          <div className="border-t bg-background/50 p-4 backdrop-blur-sm">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about San Francisco restaurants, local dishes, or dining recommendations..."
                  className={cn(
                    "w-full rounded-lg border bg-background px-4 py-2 pr-10",
                    "placeholder:text-muted-foreground/50",
                    "focus:outline-none focus:ring-2 focus:ring-primary/50",
                    "disabled:opacity-50",
                    "transition-all duration-200"
                  )}
                  disabled={isLoading}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setMessages([])}
                  className="shrink-0"
                  disabled={isLoading || messages.length === 0}
                >
                  <RefreshCw className="h-5 w-5" />
                </Button>
                <Button
                  type="submit"
                  className="shrink-0"
                  disabled={!input.trim() || isLoading}
                >
                  <Send className="h-5 w-5" />
                </Button>
              </div>
            </form>
          </div>
        </div>
      </Card>
    </div>
  );
} 
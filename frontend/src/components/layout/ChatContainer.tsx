"use client";

import React, { useRef, useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Send, Loader2 } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ScrollArea } from '../ui/scroll-area';
import type { Message } from '@/types/chat';

interface ChatContainerProps {
  className?: string;
  messages: Message[];
  isLoading?: boolean;
  onSendMessage: (message: string) => Promise<void>;
}

export function ChatContainer({
  className,
  messages,
  isLoading = false,
  onSendMessage,
}: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [input, setInput] = useState('');

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    const isScrolledToBottom = 
      Math.abs(target.scrollHeight - target.scrollTop - target.clientHeight) < 1;
    setAutoScroll(isScrolledToBottom);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    try {
      await onSendMessage(input);
      setInput('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <Card className={cn('sf-card flex flex-col h-full overflow-hidden', className)}>
      {/* Welcome Message */}
      {messages.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center p-4">
          <div className="text-center space-y-6 max-w-2xl mx-auto">
            <span className="text-8xl">🌉</span>
            <div className="space-y-4">
              <h2 className="sf-heading text-4xl">
                Welcome to SF Dining Guide
              </h2>
              <p className="text-muted-foreground text-lg max-w-md mx-auto">
                Discover the best of San Francisco's culinary scene. Ask me about local favorites, hidden gems, and iconic establishments.
              </p>
            </div>
            <div className="flex flex-col gap-3 text-sm">
              <p className="text-muted-foreground font-medium">Try asking about:</p>
              <div className="flex flex-wrap justify-center gap-2">
                {[
                  "Best dim sum in Chinatown 🥟",
                  "Mission District tacos 🌮",
                  "Seafood at Fisherman's Wharf 🦀",
                  "Hayes Valley date spots 💝",
                  "North Beach Italian 🍝",
                  "Best rooftop bars 🍸"
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="sf-suggestion"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <ScrollArea 
        className="flex-1 px-4"
        onScrollCapture={handleScroll}
      >
        <div className="flex flex-col gap-4 py-4">
          {messages.map((message, i) => (
            <ChatMessage
              key={i}
              content={message.content}
              isUser={message.role === 'user'}
              isLoading={isLoading && i === messages.length - 1}
              className="sf-message"
            />
          ))}
          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      {/* Input Form */}
      <div className="sf-glass border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about San Francisco restaurants, local dishes, or dining recommendations..."
            className="sf-input flex-1"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="sf-button"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>
    </Card>
  );
} 
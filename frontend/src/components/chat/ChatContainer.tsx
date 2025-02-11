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
  finalPrompt?: string;
  hideMessages?: boolean;
}

export function ChatContainer({
  className,
  messages,
  isLoading = false,
  onSendMessage,
  finalPrompt,
  hideMessages = false,
}: ChatContainerProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const lastMessageRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState('');
  const prevMessagesLength = useRef(messages.length);

  // Scroll to the top of new message when it arrives
  useEffect(() => {
    if (messages.length > prevMessagesLength.current && lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: 'auto', block: 'start' });
    }
    prevMessagesLength.current = messages.length;
  }, [messages]);

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
    <Card className={cn(
      'flex flex-col overflow-hidden',
      !hideMessages && 'sf-card',
      className
    )}>
      {/* Messages */}
      {!hideMessages && (
        <div className="flex-1 overflow-hidden">
          <ScrollArea 
            className="h-full px-4"
            ref={scrollAreaRef}
          >
            <div className="flex flex-col gap-4 py-4">
              {messages.map((message, i) => (
                <div
                  key={i}
                  ref={i === messages.length - 1 ? lastMessageRef : null}
                >
                  <ChatMessage
                    content={message.content}
                    isUser={message.role === 'user'}
                    isLoading={isLoading && i === messages.length - 1}
                  />
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Input Form */}
      <div className="flex-shrink-0 sf-glass border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about San Francisco restaurants, local dishes, or dining recommendations..."
            className="sf-input flex-1 sf-shine"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="sf-button sf-shine sf-press"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>
    </Card>
  );
} 
import React, { useRef, useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '../ui/Button';
import { Send, Paperclip, Command, X, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { Textarea } from '../ui/Textarea';
import { KeyboardEvent } from 'react';

interface Command {
  id: string;
  name: string;
  description: string;
  execute: () => void;
}

interface ChatInputProps {
  className?: string;
  placeholder?: string;
  maxLength?: number;
  disabled?: boolean;
  commands?: Command[];
  onSendMessage: (message: string, attachments?: File[]) => Promise<void>;
  onStartTyping?: () => void;
  onStopTyping?: () => void;
}

export function ChatInput({
  className,
  placeholder = 'Type a message...',
  maxLength = 2000,
  disabled = false,
  commands = [],
  onSendMessage,
  onStartTyping,
  onStopTyping,
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const [commandFilter, setCommandFilter] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addToast } = useToast();
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isComposing, setIsComposing] = useState(false);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [message]);

  // Handle typing notifications
  useEffect(() => {
    if (message && onStartTyping) {
      onStartTyping();
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      typingTimeoutRef.current = setTimeout(() => {
        onStopTyping?.();
      }, 1000);
    }

    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [message, onStartTyping, onStopTyping]);

  const handleSend = async () => {
    if (!message.trim() || disabled || isLoading) return;

    try {
      setIsLoading(true);
      await onSendMessage(message);
      setMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      // Validate file types and sizes here if needed
      setAttachments((prev) => [...prev, ...files]);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const filteredCommands = commands.filter((cmd) =>
    cmd.name.toLowerCase().includes(commandFilter.toLowerCase())
  );

  return (
    <div className={cn('flex items-end gap-2', className)}>
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        placeholder={placeholder}
        className="min-h-[60px] resize-none rounded-lg"
        rows={1}
        disabled={disabled}
        maxLength={maxLength}
      />
      <Button
        onClick={handleSend}
        disabled={!message.trim() || disabled || isLoading}
        size="icon"
        className="mb-[3px] h-[36px] w-[36px] shrink-0"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
} 
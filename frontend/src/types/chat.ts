export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  status?: 'sending' | 'sent' | 'error';
  error?: string;
  context?: {
    text: string;
    metadata: {
      source: 'menu' | 'wikipedia';
      title: string;
      restaurant: string;
      category: string;
      item_name: string;
      description: string;
      ingredients: string[];
      categories: string[];
      rating: number;
      review_count: number;
      price: string;
      address: string;
      position: number;
      similarity: number;
      tokens: number;
    };
  }[];
} 
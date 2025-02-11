import { useState, useEffect } from 'react';
import { WebSocketManager } from '@/lib/websocket/WebSocketManager';

interface RetrievalState {
  status: 'idle' | 'running' | 'complete' | 'error';
  progress: number;
  chunks: Array<{
    id: string;
    content: string;
    similarity: number;
  }>;
  error?: string;
}

interface PreprocessingState {
  status: 'idle' | 'running' | 'complete' | 'error';
  progress: number;
  steps: Array<{
    name: string;
    status: 'pending' | 'running' | 'complete' | 'error';
  }>;
  error?: string;
}

interface GenerationState {
  status: 'idle' | 'running' | 'complete' | 'error';
  progress: number;
  tokens: {
    generated: number;
    total: number;
  };
  error?: string;
}

interface TokenUsage {
  prompt: number;
  completion: number;
  total: number;
  cost: number;
}

interface RAGPipelineState {
  retrieval: RetrievalState;
  preprocessing: PreprocessingState;
  generation: GenerationState;
  tokenUsage: TokenUsage;
  performance: {
    retrievalTime: number;
    preprocessingTime: number;
    generationTime: number;
    totalTime: number;
  };
}

const initialState: RAGPipelineState = {
  retrieval: {
    status: 'idle',
    progress: 0,
    chunks: [],
  },
  preprocessing: {
    status: 'idle',
    progress: 0,
    steps: [
      { name: 'Tokenization', status: 'pending' },
      { name: 'Embedding', status: 'pending' },
      { name: 'Reranking', status: 'pending' },
    ],
  },
  generation: {
    status: 'idle',
    progress: 0,
    tokens: {
      generated: 0,
      total: 0,
    },
  },
  tokenUsage: {
    prompt: 0,
    completion: 0,
    total: 0,
    cost: 0,
  },
  performance: {
    retrievalTime: 0,
    preprocessingTime: 0,
    generationTime: 0,
    totalTime: 0,
  },
};

export function useRAGPipeline(websocketUrl: string) {
  const [state, setState] = useState<RAGPipelineState>(initialState);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocketManager(websocketUrl);

    // Retrieval events
    ws.addEventListener('retrieval_start', () => {
      setState(prev => ({
        ...prev,
        retrieval: {
          ...prev.retrieval,
          status: 'running',
          progress: 0,
        },
      }));
    });

    ws.addEventListener('retrieval_progress', (event) => {
      setState(prev => ({
        ...prev,
        retrieval: {
          ...prev.retrieval,
          progress: event.data.progress,
          chunks: event.data.chunks,
        },
      }));
    });

    ws.addEventListener('retrieval_complete', (event) => {
      setState(prev => ({
        ...prev,
        retrieval: {
          ...prev.retrieval,
          status: 'complete',
          progress: 100,
          chunks: event.data.chunks,
        },
        performance: {
          ...prev.performance,
          retrievalTime: event.data.time,
        },
      }));
    });

    // Preprocessing events
    ws.addEventListener('preprocessing_start', () => {
      setState(prev => ({
        ...prev,
        preprocessing: {
          ...prev.preprocessing,
          status: 'running',
          progress: 0,
        },
      }));
    });

    ws.addEventListener('preprocessing_progress', (event) => {
      setState(prev => ({
        ...prev,
        preprocessing: {
          ...prev.preprocessing,
          progress: event.data.progress,
          steps: event.data.steps,
        },
      }));
    });

    ws.addEventListener('preprocessing_complete', (event) => {
      setState(prev => ({
        ...prev,
        preprocessing: {
          ...prev.preprocessing,
          status: 'complete',
          progress: 100,
          steps: prev.preprocessing.steps.map(step => ({
            ...step,
            status: 'complete',
          })),
        },
        performance: {
          ...prev.performance,
          preprocessingTime: event.data.time,
        },
      }));
    });

    // Generation events
    ws.addEventListener('generation_start', () => {
      setState(prev => ({
        ...prev,
        generation: {
          ...prev.generation,
          status: 'running',
          progress: 0,
        },
      }));
    });

    ws.addEventListener('generation_progress', (event) => {
      setState(prev => ({
        ...prev,
        generation: {
          ...prev.generation,
          progress: event.data.progress,
          tokens: event.data.tokens,
        },
      }));
    });

    ws.addEventListener('generation_complete', (event) => {
      setState(prev => ({
        ...prev,
        generation: {
          ...prev.generation,
          status: 'complete',
          progress: 100,
        },
        performance: {
          ...prev.performance,
          generationTime: event.data.time,
          totalTime: event.data.totalTime,
        },
      }));
    });

    // Token usage events
    ws.addEventListener('token_usage', (event) => {
      setState(prev => ({
        ...prev,
        tokenUsage: event.data,
      }));
    });

    // Error handling
    ws.addEventListener('error', (event) => {
      setError(event.data.message);
      setState(prev => ({
        ...prev,
        retrieval: { ...prev.retrieval, status: 'error', error: event.data.message },
        preprocessing: { ...prev.preprocessing, status: 'error', error: event.data.message },
        generation: { ...prev.generation, status: 'error', error: event.data.message },
      }));
    });

    return () => {
      ws.disconnect();
    };
  }, [websocketUrl]);

  const reset = () => {
    setState(initialState);
    setError(null);
  };

  return {
    state,
    error,
    reset,
  };
} 
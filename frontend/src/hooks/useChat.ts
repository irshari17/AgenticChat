/**
 * React hook for managing chat state and WebSocket communication.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { ChatWebSocket, WSMessage } from '../services/websocket';

export interface ChatMessageUI {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  type?: string;
  timestamp: Date;
  isStreaming?: boolean;
  metadata?: Record<string, any>;
}

interface UseChatReturn {
  messages: ChatMessageUI[];
  sendMessage: (text: string) => void;
  isConnected: boolean;
  isLoading: boolean;
  sessionId: string | null;
  error: string | null;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessageUI[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<ChatWebSocket | null>(null);
  const streamingContentRef = useRef<string>('');
  const messageIdCounter = useRef(0);

  const generateId = () => {
    messageIdCounter.current++;
    return `msg-${Date.now()}-${messageIdCounter.current}`;
  };

  // Initialize WebSocket connection
  useEffect(() => {
    const ws = new ChatWebSocket('new');
    wsRef.current = ws;

    // Handle all message types
    ws.on('*', (msg: WSMessage) => {
      handleWSMessage(msg);
    });

    ws.on('connected', () => {
      setIsConnected(true);
      setError(null);
    });

    ws.on('disconnected', () => {
      setIsConnected(false);
    });

    // Connect
    ws.connect()
      .then((sid) => {
        setSessionId(sid);
        setIsConnected(true);
      })
      .catch((err) => {
        setError('Failed to connect to server');
        console.error('Connection failed:', err);
      });

    return () => {
      ws.disconnect();
    };
  }, []);

  const handleWSMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'status':
        // Add status messages as system messages
        if (!msg.content.startsWith('Connected')) {
          setMessages((prev) => [
            ...prev,
            {
              id: generateId(),
              role: 'system',
              content: msg.content,
              type: 'status',
              timestamp: new Date(),
            },
          ]);
        }
        break;

      case 'plan':
        // Show the plan
        try {
          const plan = JSON.parse(msg.content);
          const planText = formatPlan(plan);
          setMessages((prev) => [
            ...prev,
            {
              id: generateId(),
              role: 'system',
              content: planText,
              type: 'plan',
              timestamp: new Date(),
            },
          ]);
        } catch {
          // Ignore parse errors
        }
        break;

      case 'task_update':
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'system',
            content: msg.content,
            type: 'task_update',
            timestamp: new Date(),
          },
        ]);
        break;

      case 'tool_call':
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'tool',
            content: msg.content,
            type: 'tool_call',
            timestamp: new Date(),
          },
        ]);
        break;

      case 'tool_result':
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'tool',
            content: msg.content,
            type: 'tool_result',
            timestamp: new Date(),
          },
        ]);
        break;

      case 'stream_start':
        streamingContentRef.current = '';
        setMessages((prev) => [
          ...prev,
          {
            id: 'streaming',
            role: 'assistant',
            content: '',
            isStreaming: true,
            timestamp: new Date(),
          },
        ]);
        break;

      case 'assistant_chunk':
        streamingContentRef.current += msg.content;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === 'streaming'
              ? { ...m, content: streamingContentRef.current }
              : m
          )
        );
        break;

      case 'stream_end':
        setMessages((prev) =>
          prev.map((m) =>
            m.id === 'streaming'
              ? { ...m, id: generateId(), isStreaming: false }
              : m
          )
        );
        break;

      case 'assistant_message':
        // Final complete message — replace streaming if exists, otherwise add
        setMessages((prev) => {
          const hasStreaming = prev.some((m) => m.id === 'streaming');
          if (hasStreaming) {
            return prev.map((m) =>
              m.id === 'streaming'
                ? {
                    ...m,
                    id: generateId(),
                    content: msg.content,
                    isStreaming: false,
                    metadata: msg.metadata,
                  }
                : m
            );
          }
          // Only add if content differs from last assistant message
          const lastAssistant = [...prev].reverse().find(m => m.role === 'assistant');
          if (lastAssistant && lastAssistant.content === msg.content) {
            return prev; // Skip duplicate
          }
          return [
            ...prev,
            {
              id: generateId(),
              role: 'assistant',
              content: msg.content,
              timestamp: new Date(),
              metadata: msg.metadata,
            },
          ];
        });
        setIsLoading(false);
        break;

      case 'error':
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'system',
            content: `❌ ${msg.content}`,
            type: 'error',
            timestamp: new Date(),
          },
        ]);
        setIsLoading(false);
        setError(msg.content);
        break;
    }
  }, []);

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim() || !wsRef.current?.isConnected()) return;

      // Add user message
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: 'user',
          content: text,
          timestamp: new Date(),
        },
      ]);

      setIsLoading(true);
      setError(null);
      wsRef.current.sendMessage(text);
    },
    []
  );

  return {
    messages,
    sendMessage,
    isConnected,
    isLoading,
    sessionId,
    error,
  };
}

function formatPlan(plan: any): string {
  let text = `📋 **Plan**: ${plan.reasoning || 'Executing plan...'}\n`;
  if (plan.steps && plan.steps.length > 0) {
    plan.steps.forEach((step: any, i: number) => {
      const icon = step.type === 'tool' ? '🔧' : '🤖';
      const label = step.tool || step.task || 'Step';
      text += `  ${i + 1}. ${icon} ${label}: ${step.reasoning || ''}\n`;
    });
  }
  return text;
}

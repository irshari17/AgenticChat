/**
 * WebSocket service for communicating with the backend agent system.
 * v2: Added agent_status and coordinator message types.
 */

export type MessageType =
  | 'user_message'
  | 'assistant_chunk'
  | 'assistant_message'
  | 'tool_call'
  | 'tool_result'
  | 'plan'
  | 'task_update'
  | 'agent_status'
  | 'coordinator'
  | 'error'
  | 'status'
  | 'stream_start'
  | 'stream_end';

export interface WSMessage {
  type: MessageType;
  content: string;
  session_id: string;
  metadata?: Record<string, any>;
}

export type MessageHandler = (message: WSMessage) => void;

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private intentionalClose = false;

  constructor(sessionId: string = 'new') {
    this.sessionId = sessionId;
  }

  connect(): Promise<string> {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const url = `${protocol}//${host}/ws/chat/${this.sessionId}`;

      try {
        this.ws = new WebSocket(url);
      } catch (err) {
        reject(err);
        return;
      }

      this.ws.onopen = () => {
        console.log('[WS] Connected');
        this.reconnectAttempts = 0;
        this.intentionalClose = false;
        this.emit('connected', {
          type: 'status',
          content: 'Connected',
          session_id: this.sessionId,
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);

          if (msg.session_id && msg.session_id !== this.sessionId) {
            this.sessionId = msg.session_id;
          }

          if (msg.type === 'status' && msg.content.startsWith('Connected')) {
            resolve(msg.session_id);
          }

          this.emit(msg.type, msg);
          this.emit('*', msg);
        } catch (err) {
          console.error('[WS] Failed to parse message:', err);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        this.emit('error', {
          type: 'error',
          content: 'WebSocket connection error',
          session_id: this.sessionId,
        });
      };

      this.ws.onclose = () => {
        console.log('[WS] Closed');
        this.emit('disconnected', {
          type: 'status',
          content: 'Disconnected',
          session_id: this.sessionId,
        });
        if (!this.intentionalClose) {
          this.attemptReconnect();
        }
      };

      setTimeout(() => {
        if (this.ws?.readyState !== WebSocket.OPEN) {
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });
  }

  sendMessage(message: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message }));
    } else {
      console.error('[WS] Not connected');
    }
  }

  on(event: string, handler: MessageHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  off(event: string, handler: MessageHandler) {
    const handlers = this.handlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(event: string, message: WSMessage) {
    const handlers = this.handlers.get(event) || [];
    handlers.forEach((handler) => handler(message));
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => {
        this.connect().catch(() => {});
      }, delay);
    }
  }

  disconnect() {
    this.intentionalClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  getSessionId(): string {
    return this.sessionId;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

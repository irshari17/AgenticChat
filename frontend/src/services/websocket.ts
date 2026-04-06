/**
 * WebSocket service for communicating with the backend agent system.
 */

export type MessageType =
  | 'user_message'
  | 'assistant_chunk'
  | 'assistant_message'
  | 'tool_call'
  | 'tool_result'
  | 'plan'
  | 'task_update'
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

export type WSEventHandler = (message: WSMessage) => void;

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private handlers: Map<string, WSEventHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(sessionId: string = 'new') {
    this.sessionId = sessionId;
  }

  /**
   * Connect to the WebSocket server.
   */
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
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected', {
          type: 'status',
          content: 'Connected',
          session_id: this.sessionId,
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);

          // Update session ID from server
          if (msg.session_id && msg.session_id !== this.sessionId) {
            this.sessionId = msg.session_id;
          }

          // If this is the initial status with session ID, resolve
          if (msg.type === 'status' && msg.content.startsWith('Connected')) {
            resolve(msg.session_id);
          }

          // Emit to type-specific handlers
          this.emit(msg.type, msg);
          // Emit to catch-all handlers
          this.emit('*', msg);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', {
          type: 'error',
          content: 'WebSocket connection error',
          session_id: this.sessionId,
        });
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this.emit('disconnected', {
          type: 'status',
          content: 'Disconnected',
          session_id: this.sessionId,
        });
        this.attemptReconnect();
      };

      // Timeout for initial connection
      setTimeout(() => {
        if (this.ws?.readyState !== WebSocket.OPEN) {
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });
  }

  /**
   * Send a message to the server.
   */
  sendMessage(message: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message }));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  /**
   * Register an event handler.
   */
  on(event: string, handler: WSEventHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  /**
   * Remove an event handler.
   */
  off(event: string, handler: WSEventHandler) {
    const handlers = this.handlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Emit an event to all registered handlers.
   */
  private emit(event: string, message: WSMessage) {
    const handlers = this.handlers.get(event) || [];
    handlers.forEach((handler) => handler(message));
  }

  /**
   * Attempt to reconnect after disconnection.
   */
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => {
        this.connect().catch(() => {});
      }, delay);
    }
  }

  /**
   * Disconnect from the server.
   */
  disconnect() {
    this.maxReconnectAttempts = 0; // Prevent reconnection
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Get the current session ID.
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * Check if the WebSocket is connected.
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

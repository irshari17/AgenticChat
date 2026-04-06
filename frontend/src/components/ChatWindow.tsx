import React, { useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import Message from './Message';
import InputBox from './InputBox';

const ChatWindow: React.FC = () => {
  const { messages, sendMessage, isConnected, isLoading, sessionId, error } =
    useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        overflow: 'hidden',
      }}
    >
      {/* Connection Status Bar */}
      <div
        style={{
          padding: '6px 24px',
          fontSize: '12px',
          backgroundColor: isConnected ? '#0d2818' : '#2d1117',
          color: isConnected ? '#3fb950' : '#f85149',
          borderBottom: '1px solid #2a2a2a',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#3fb950' : '#f85149',
            display: 'inline-block',
          }}
        />
        {isConnected
          ? `Connected • Session: ${sessionId?.slice(0, 8) || '...'}...`
          : 'Disconnected — Attempting to reconnect...'}
      </div>

      {/* Messages Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
              color: '#666',
              textAlign: 'center',
              gap: '12px',
            }}
          >
            <div style={{ fontSize: '48px' }}>🤖</div>
            <h2 style={{ fontSize: '20px', color: '#999' }}>
              Agentic AI Chat
            </h2>
            <p style={{ fontSize: '14px', maxWidth: '400px' }}>
              I can help you with tasks using tools like file operations, web
              fetching, and shell commands. Try asking me something!
            </p>
            <div
              style={{
                display: 'flex',
                gap: '8px',
                flexWrap: 'wrap',
                justifyContent: 'center',
                marginTop: '12px',
              }}
            >
              {[
                'List files in the current directory',
                'What is the weather API?',
                'Write a hello.txt file',
                'Explain how LangGraph works',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#1a1a2e',
                    border: '1px solid #333',
                    borderRadius: '20px',
                    color: '#aaa',
                    cursor: 'pointer',
                    fontSize: '13px',
                    transition: 'all 0.2s',
                  }}
                  onMouseOver={(e) => {
                    (e.target as HTMLButtonElement).style.borderColor = '#667eea';
                    (e.target as HTMLButtonElement).style.color = '#fff';
                  }}
                  onMouseOut={(e) => {
                    (e.target as HTMLButtonElement).style.borderColor = '#333';
                    (e.target as HTMLButtonElement).style.color = '#aaa';
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <Message key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: '#888',
              fontSize: '14px',
              padding: '8px 0',
            }}
          >
            <div className="loading-dots">
              <span style={{ animation: 'blink 1.4s infinite both' }}>●</span>
              <span
                style={{ animation: 'blink 1.4s infinite both 0.2s' }}
              >
                ●
              </span>
              <span
                style={{ animation: 'blink 1.4s infinite both 0.4s' }}
              >
                ●
              </span>
            </div>
            <span>Thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <InputBox onSend={sendMessage} disabled={!isConnected || isLoading} />

      {/* CSS Animations */}
      <style>{`
        @keyframes blink {
          0%, 80%, 100% { opacity: 0; }
          40% { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default ChatWindow;

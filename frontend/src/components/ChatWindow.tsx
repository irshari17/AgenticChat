import React, { useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import Message from './Message';
import InputBox from './InputBox';
import AgentActivity from './AgentActivity';

const ChatWindow: React.FC = () => {
  const { messages, agentEvents, sendMessage, isConnected, isLoading, sessionId, error } =
    useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
          padding: '5px 24px',
          fontSize: '11px',
          backgroundColor: isConnected ? '#0a1f14' : '#2d1117',
          color: isConnected ? '#3fb950' : '#f85149',
          borderBottom: '1px solid #1e1e2e',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#3fb950' : '#f85149',
            display: 'inline-block',
          }}
        />
        {isConnected
          ? `Connected \u2022 Session: ${sessionId?.slice(0, 8) || '...'}...`
          : 'Disconnected \u2014 Attempting to reconnect...'}
      </div>

      {/* Messages Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
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
              color: '#555',
              textAlign: 'center',
              gap: '12px',
            }}
          >
            <div style={{ fontSize: '48px', opacity: 0.7 }}>\ud83e\udd16</div>
            <h2 style={{ fontSize: '20px', color: '#888' }}>
              Agentic AI Chat <span style={{ color: '#667eea', fontSize: '14px' }}>v2</span>
            </h2>
            <p style={{ fontSize: '13px', maxWidth: '420px', color: '#666' }}>
              Multi-agent system with Coordinator, Planner, and Executor.
              I can use tools like file operations, web fetching, and shell commands.
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
                'List files in the sandbox',
                'Fetch https://httpbin.org/json',
                'Write a hello.txt file',
                'What can you do?',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#111',
                    border: '1px solid #2a2a3a',
                    borderRadius: '20px',
                    color: '#999',
                    cursor: 'pointer',
                    fontSize: '12px',
                    transition: 'all 0.2s',
                  }}
                  onMouseOver={(e) => {
                    (e.target as HTMLButtonElement).style.borderColor = '#667eea';
                    (e.target as HTMLButtonElement).style.color = '#ddd';
                  }}
                  onMouseOut={(e) => {
                    (e.target as HTMLButtonElement).style.borderColor = '#2a2a3a';
                    (e.target as HTMLButtonElement).style.color = '#999';
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

        {/* Agent Activity indicator */}
        {isLoading && agentEvents.length > 0 && (
          <AgentActivity events={agentEvents} />
        )}

        {isLoading && agentEvents.length === 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: '#666',
              fontSize: '13px',
              padding: '8px 0',
            }}
          >
            <div className="loading-dots">
              <span style={{ animation: 'blink 1.4s infinite both' }}>\u25cf</span>
              <span style={{ animation: 'blink 1.4s infinite both 0.2s' }}>\u25cf</span>
              <span style={{ animation: 'blink 1.4s infinite both 0.4s' }}>\u25cf</span>
            </div>
            <span>Processing...</span>
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

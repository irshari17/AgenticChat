import React from 'react';
import ChatWindow from './components/ChatWindow';

const App: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        backgroundColor: '#0a0a0f',
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: '14px 24px',
          borderBottom: '1px solid #1e1e2e',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'linear-gradient(135deg, #0d0d1a 0%, #111827 100%)',
        }}
      >
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '18px',
          }}
        >
          🤖
        </div>
        <div>
          <h1
            style={{
              fontSize: '18px',
              fontWeight: 700,
              color: '#ffffff',
              lineHeight: 1.2,
            }}
          >
            Agentic AI Chat <span style={{ fontSize: '11px', color: '#667eea', fontWeight: 400 }}>v2</span>
          </h1>
          <p
            style={{
              fontSize: '11px',
              color: '#666',
              lineHeight: 1.2,
            }}
          >
            Coordinator → Planner → Executor • LangGraph • Qwen 3
          </p>
        </div>
      </header>

      {/* Chat */}
      <ChatWindow />
    </div>
  );
};

export default App;

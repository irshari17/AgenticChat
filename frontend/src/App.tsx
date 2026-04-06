import React from 'react';
import ChatWindow from './components/ChatWindow';

const App: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        backgroundColor: '#0f0f0f',
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: '16px 24px',
          borderBottom: '1px solid #2a2a2a',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
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
            Agentic AI Chat
          </h1>
          <p
            style={{
              fontSize: '12px',
              color: '#888',
              lineHeight: 1.2,
            }}
          >
            Powered by LangGraph • Qwen 3 • OpenRouter
          </p>
        </div>
      </header>

      {/* Chat */}
      <ChatWindow />
    </div>
  );
};

export default App;

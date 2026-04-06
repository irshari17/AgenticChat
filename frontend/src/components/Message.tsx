import React from 'react';
import { ChatMessageUI } from '../hooks/useChat';

interface MessageProps {
  message: ChatMessageUI;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const { role, content, type, isStreaming } = message;

  // Style based on role and type
  const getStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      padding: '12px 16px',
      borderRadius: '12px',
      maxWidth: '85%',
      fontSize: '14px',
      lineHeight: '1.6',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word',
    };

    switch (role) {
      case 'user':
        return {
          ...base,
          alignSelf: 'flex-end',
          backgroundColor: '#1a3a5c',
          color: '#e0e0e0',
          borderBottomRightRadius: '4px',
        };
      case 'assistant':
        return {
          ...base,
          alignSelf: 'flex-start',
          backgroundColor: '#1e1e2e',
          color: '#e0e0e0',
          borderBottomLeftRadius: '4px',
          border: '1px solid #2a2a3a',
        };
      case 'system':
        return {
          ...base,
          alignSelf: 'center',
          backgroundColor:
            type === 'error'
              ? '#2d1117'
              : type === 'plan'
              ? '#1a1a2e'
              : '#161616',
          color:
            type === 'error'
              ? '#f85149'
              : type === 'plan'
              ? '#b8b8ff'
              : '#888',
          fontSize: '12px',
          maxWidth: '95%',
          border:
            type === 'plan'
              ? '1px solid #333366'
              : type === 'error'
              ? '1px solid #5c1d1d'
              : '1px solid #222',
        };
      case 'tool':
        return {
          ...base,
          alignSelf: 'flex-start',
          backgroundColor: '#0d2818',
          color: '#8bc48a',
          fontSize: '12px',
          fontFamily: 'monospace',
          maxWidth: '95%',
          border: '1px solid #1a4028',
        };
      default:
        return base;
    }
  };

  const getIcon = (): string => {
    switch (role) {
      case 'user':
        return '👤';
      case 'assistant':
        return '🤖';
      case 'system':
        return type === 'plan'
          ? '📋'
          : type === 'task_update'
          ? '⚙️'
          : type === 'error'
          ? '❌'
          : 'ℹ️';
      case 'tool':
        return type === 'tool_call' ? '🔧' : '📊';
      default:
        return '💬';
    }
  };

  const getRoleLabel = (): string => {
    switch (role) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'AI Agent';
      case 'system':
        return type === 'plan'
          ? 'Planner'
          : type === 'task_update'
          ? 'Executor'
          : 'System';
      case 'tool':
        return 'Tool';
      default:
        return role;
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        ...getStyles(),
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginBottom: '4px',
          fontSize: '11px',
          color: '#888',
        }}
      >
        <span>{getIcon()}</span>
        <span style={{ fontWeight: 600 }}>{getRoleLabel()}</span>
        {isStreaming && (
          <span
            style={{
              color: '#667eea',
              fontSize: '10px',
              marginLeft: '4px',
            }}
          >
            ● streaming
          </span>
        )}
      </div>

      {/* Content */}
      <div>{content}</div>

      {/* Cursor for streaming */}
      {isStreaming && (
        <span
          style={{
            display: 'inline-block',
            width: '2px',
            height: '16px',
            backgroundColor: '#667eea',
            marginLeft: '2px',
            animation: 'blink 1s infinite',
          }}
        />
      )}
    </div>
  );
};

export default Message;

import React, { useState, useRef, useEffect } from 'react';

interface InputBoxProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const InputBox: React.FC<InputBoxProps> = ({ onSend, disabled = false }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        padding: '14px 24px',
        borderTop: '1px solid #1e1e2e',
        backgroundColor: '#0d0d14',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-end',
          maxWidth: '900px',
          margin: '0 auto',
        }}
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'Processing...' : 'Type your message... (Shift+Enter for new line)'}
          disabled={disabled}
          rows={1}
          style={{
            flex: 1,
            padding: '12px 16px',
            backgroundColor: '#111119',
            border: '1px solid #252538',
            borderRadius: '12px',
            color: '#e0e0e0',
            fontSize: '14px',
            fontFamily: 'inherit',
            resize: 'none',
            outline: 'none',
            lineHeight: '1.5',
            transition: 'border-color 0.2s',
            minHeight: '44px',
            maxHeight: '200px',
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#667eea';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#252538';
          }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          style={{
            padding: '12px 20px',
            backgroundColor:
              disabled || !input.trim() ? '#1a1a28' : '#667eea',
            color: disabled || !input.trim() ? '#555' : '#fff',
            border: 'none',
            borderRadius: '12px',
            cursor: disabled || !input.trim() ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 600,
            transition: 'all 0.2s',
            minHeight: '44px',
            whiteSpace: 'nowrap',
          }}
          onMouseOver={(e) => {
            if (!disabled && input.trim()) {
              (e.target as HTMLButtonElement).style.backgroundColor = '#7c8ef7';
            }
          }}
          onMouseOut={(e) => {
            if (!disabled && input.trim()) {
              (e.target as HTMLButtonElement).style.backgroundColor = '#667eea';
            }
          }}
        >
          Send \u27a4
        </button>
      </div>
      <div
        style={{
          textAlign: 'center',
          fontSize: '10px',
          color: '#444',
          marginTop: '8px',
        }}
      >
        Agentic AI Chat v2 \u2022 Coordinator \u2192 Planner \u2192 Executor
      </div>
    </div>
  );
};

export default InputBox;

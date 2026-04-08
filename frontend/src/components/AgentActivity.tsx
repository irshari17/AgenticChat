import React from 'react';
import { AgentEvent } from '../hooks/useChat';

interface Props {
  events: AgentEvent[];
}

const agentStyles: Record<string, { icon: string; color: string }> = {
  coordinator: { icon: '\ud83c\udfaf', color: '#f59e0b' },
  planner: { icon: '\ud83d\udccb', color: '#8b5cf6' },
  executor: { icon: '\u2699\ufe0f', color: '#3b82f6' },
  tool: { icon: '\ud83d\udd27', color: '#10b981' },
  memory: { icon: '\ud83e\udde0', color: '#14b8a6' },
  system: { icon: '\u2139\ufe0f', color: '#6b7280' },
};

const AgentActivity: React.FC<Props> = ({ events }) => {
  if (events.length === 0) return null;

  return (
    <div style={{
      margin: '0 0 12px 0',
      padding: '10px 14px',
      backgroundColor: '#0d0d1a',
      borderRadius: '10px',
      border: '1px solid #1e1e2e',
      fontSize: '12px',
      maxHeight: '200px',
      overflowY: 'auto',
    }}>
      <div style={{
        fontSize: '10px',
        color: '#6366f1',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        marginBottom: '6px',
      }}>
        Agent Activity
      </div>

      {events.map((event, i) => {
        const style = agentStyles[event.agent] || { icon: '\u2022', color: '#666' };
        return (
          <div key={i} style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '6px',
            padding: '3px 0',
            color: style.color,
            lineHeight: 1.4,
          }}>
            <span style={{ flexShrink: 0 }}>{style.icon}</span>
            <span style={{ color: '#999', wordBreak: 'break-word' }}>
              {event.status.length > 200 ? event.status.slice(0, 200) + '...' : event.status}
            </span>
          </div>
        );
      })}

      <div style={{ color: '#6366f1', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
        <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>\u27f3</span>
        Processing...
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AgentActivity;

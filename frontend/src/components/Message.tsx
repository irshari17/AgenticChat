import React from "react";
import { ChatMessageUI } from "../hooks/useChat";

interface MessageProps {
  message: ChatMessageUI;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const { role, content, type, isStreaming } = message;

  const getStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      padding: "12px 16px",
      borderRadius: "12px",
      maxWidth: "85%",
      fontSize: "14px",
      lineHeight: "1.6",
      whiteSpace: "pre-wrap",
      wordBreak: "break-word",
    };

    switch (role) {
      case "user":
        return {
          ...base,
          alignSelf: "flex-end",
          backgroundColor: "#1a3a5c",
          color: "#e0e0e0",
          borderBottomRightRadius: "4px",
        };
      case "assistant":
        return {
          ...base,
          alignSelf: "flex-start",
          backgroundColor: "#1a1a28",
          color: "#e0e0e0",
          borderBottomLeftRadius: "4px",
          border: "1px solid #252538",
        };
      case "coordinator":
        return {
          ...base,
          alignSelf: "center",
          backgroundColor: "#1a1428",
          color: "#c4b5fd",
          fontSize: "12px",
          maxWidth: "90%",
          border: "1px solid #2d2250",
        };
      case "system":
        return {
          ...base,
          alignSelf: "center",
          backgroundColor:
            type === "error" ? "#2d1117" : type === "plan" ? "#111122" : "#111",
          color:
            type === "error" ? "#f85149" : type === "plan" ? "#b8b8ff" : "#777",
          fontSize: "12px",
          maxWidth: "95%",
          border:
            type === "plan"
              ? "1px solid #2a2a55"
              : type === "error"
                ? "1px solid #5c1d1d"
                : "1px solid #1e1e2e",
        };
      case "tool":
        return {
          ...base,
          alignSelf: "flex-start",
          backgroundColor: "#0a1f14",
          color: "#7ab87a",
          fontSize: "12px",
          fontFamily: "monospace",
          maxWidth: "95%",
          border: "1px solid #163525",
        };
      default:
        return base;
    }
  };

  const getIcon = (): string => {
    switch (role) {
      case "user":
        return "\ud83d\udc64";
      case "assistant":
        return "\ud83e\udd16";
      case "coordinator":
        return "\ud83c\udfaf";
      case "system":
        return type === "plan"
          ? "\ud83d\udccb"
          : type === "task_update"
            ? "\u2699\ufe0f"
            : type === "error"
              ? "\u274c"
              : "\u2139\ufe0f";
      case "tool":
        return type === "tool_call" ? "\ud83d\udd27" : "\ud83d\udcca";
      default:
        return "\ud83d\udcac";
    }
  };

  const getRoleLabel = (): string => {
    switch (role) {
      case "user":
        return "You";
      case "assistant":
        return "AI Agent";
      case "coordinator":
        return "Coordinator";
      case "system":
        return type === "plan"
          ? "Planner"
          : type === "task_update"
            ? "Executor"
            : "System";
      case "tool":
        return "Tool";
      default:
        return role;
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        ...getStyles(),
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          marginBottom: "4px",
          fontSize: "11px",
          color: "#777",
        }}
      >
        <span>{getIcon()}</span>
        <span style={{ fontWeight: 600 }}>{getRoleLabel()}</span>
        {isStreaming && (
          <span
            style={{
              color: "#667eea",
              fontSize: "10px",
              marginLeft: "4px",
            }}
          >
            \u25cf streaming
          </span>
        )}
      </div>

      {/* Content */}
      <div>{content}</div>

      {/* Cursor for streaming */}
      {isStreaming && (
        <span
          style={{
            display: "inline-block",
            width: "2px",
            height: "16px",
            backgroundColor: "#667eea",
            marginLeft: "2px",
            animation: "blink 1s infinite",
          }}
        />
      )}
    </div>
  );
};

export default Message;

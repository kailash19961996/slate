/**
 * ChatInterface.jsx - Pretty Chat Interface Component (Markdown-ready)
 * =================================================
 * - Renders AI messages as Markdown (ReactMarkdown + GFM)
 * - Keeps user messages as plain text
 * - Typing indicator, scroll-to-bottom, clean layout
 */

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import "./ChatInterface.css";

const ChatInterface = ({ messages, onSendMessage, isLoading, onBack }) => {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue("");
    }
  };

  const formatTime = (ts) =>
    new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="chat-interface" role="region" aria-label="Chat interface">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-title">
          <Bot size={20} />
          <span>SLATE Assistant</span>
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <Bot size={48} />
            <h3>Welcome to SLATE!</h3>
            <p>I'm your AI blockchain assistant. Ask me anything!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`message ${message.sender}`}>
              <div className="message-avatar">
                {message.sender === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>

              <div className="message-content">
                <div className="message-bubble">
                  {message.sender === "ai" ? (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeSanitize]}
                      components={{
                        h1: (props) => <h1 className="md-h1" {...props} />,
                        h2: (props) => <h2 className="md-h2" {...props} />,
                        h3: (props) => <h3 className="md-h3" {...props} />,
                        p: (props) => <p className="md-p" {...props} />,
                        ul: (props) => <ul className="md-ul" {...props} />,
                        ol: (props) => <ol className="md-ol" {...props} />,
                        li: (props) => <li className="md-li" {...props} />,
                        code: ({ inline, ...props }) =>
                          inline ? (
                            <code className="md-code-inline" {...props} />
                          ) : (
                            <pre className="md-code-block">
                              <code {...props} />
                            </pre>
                          ),
                      }}
                    >
                      {message.text}
                    </ReactMarkdown>
                  ) : (
                    <p>{message.text}</p>
                  )}
                </div>

                <div className="message-time">{formatTime(message.timestamp)}</div>
              </div>
            </div>
          ))
        )}

        {/* Typing Indicator */}
        {isLoading && (
          <div className="message ai">
            <div className="message-avatar">
              <Bot size={16} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-container">
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-wrapper">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message..."
              className="message-input"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="send-button"
              disabled={!inputValue.trim() || isLoading}
              aria-label="Send message"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;

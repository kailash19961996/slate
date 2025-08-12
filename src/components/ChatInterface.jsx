import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import './ChatInterface.css'

const ChatInterface = ({ messages, onSendMessage, isConnected = true }) => {
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Simulate typing indicator
    if (messages.length > 0 && messages[messages.length - 1].sender === 'user') {
      setIsTyping(true)
      const timer = setTimeout(() => setIsTyping(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim())
      setInputValue('')
      inputRef.current?.focus()
    }
  }

  const formatTimestamp = (timestamp) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(timestamp)
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="chat-title">
          <div className="chat-icon">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2>Slate</h2>
            <span className="status-indicator">
              <div className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></div>
              {isConnected ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
        <div className="chat-actions">
          <button className="action-btn">
            <Sparkles className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="messages-container">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className={`message ${message.sender}`}
            >
              <div className="message-avatar">
                {message.sender === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </div>
              <div className="message-content">
                <div className="message-bubble">
                  <p>{message.text}</p>
                </div>
                <span className="message-time">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="message ai typing"
          >
            <div className="message-avatar">
              <Bot className="w-4 h-4" />
            </div>
            <div className="message-content">
              <div className="message-bubble">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-container">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about crypto markets, DeFi protocols, or any blockchain data..."
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="send-btn"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  )
}

export default ChatInterface
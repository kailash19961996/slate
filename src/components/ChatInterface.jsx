import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Sparkles, ArrowLeft, Wallet, CheckCircle } from 'lucide-react'
import './ChatInterface.css'

const ChatInterface = ({ 
  messages, 
  onSendMessage, 
  isConnected = true, 
  walletConnected = false,
  walletInfo = null,
  pendingInput = null,
  onBack 
}) => {
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

  const getPlaceholderText = () => {
    if (pendingInput) {
      return pendingInput.prompt || "Please provide the requested information..."
    }
    if (walletConnected) {
      return "Ask about your portfolio, DeFi opportunities, or any blockchain question..."
    }
    return "Ask about crypto markets, DeFi protocols, wallet connection, or any blockchain data..."
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="chat-header-left">
          {onBack && (
            <button onClick={onBack} className="back-btn">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
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
        </div>
        
        <div className="chat-header-right">
          {walletConnected && walletInfo && (
            <div className="wallet-status">
              <Wallet className="w-4 h-4" />
              <span className="wallet-address">{walletInfo.formatted_address || walletInfo.address}</span>
              <CheckCircle className="w-4 h-4 text-green-400" />
            </div>
          )}
          <div className="chat-actions">
            <button className="action-btn">
              <Sparkles className="w-4 h-4" />
            </button>
          </div>
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
                  {message.needsUserInput && (
                    <div className="input-request">
                      <div className="input-request-icon">
                        <Wallet className="w-4 h-4" />
                      </div>
                      <span>Waiting for your input...</span>
                    </div>
                  )}
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

        {pendingInput && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="pending-input-notice"
          >
            <div className="pending-icon">
              <Wallet className="w-5 h-5" />
            </div>
            <div className="pending-content">
              <h4>Input Required</h4>
              <p>{pendingInput.prompt}</p>
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
            placeholder={getPlaceholderText()}
            className={`chat-input ${pendingInput ? 'pending' : ''}`}
          />
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="send-btn"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        
        {pendingInput && (
          <div className="input-helper">
            <span className="helper-text">
              {pendingInput.type === 'wallet_address' && 
                "Enter your TRON wallet address (starts with 'T', 34 characters)"
              }
            </span>
          </div>
        )}
      </form>
    </div>
  )
}

export default ChatInterface
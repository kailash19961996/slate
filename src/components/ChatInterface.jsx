/**
 * ChatInterface.jsx - Pretty Chat Interface Component
 * =================================================
 * 
 * Beautiful chatbot interface featuring:
 * - Message display with user/AI distinction
 * - Typing indicator when AI is thinking
 * - Input field with send button
 * - Scroll to bottom functionality
 * - Back button to return to FirstPage
 * 
 * Connected to backend for real-time chat functionality
 */

import { useState, useRef, useEffect } from 'react'
import { Send, ArrowLeft, Bot, User } from 'lucide-react'
import './ChatInterface.css'

const ChatInterface = ({ messages, onSendMessage, isLoading, onBack }) => {
  console.log('💬 [CHAT INTERFACE] ChatInterface component rendering')
  console.log('📊 [CHAT INTERFACE] Current messages count:', messages.length)
  console.log('⏳ [CHAT INTERFACE] Is loading:', isLoading)
  
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef(null)

  /**
   * Auto-scroll to bottom when new messages are added
   */
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  /**
   * Scroll to bottom of messages container
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  /**
   * Handle message submission
   */
  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('📤 [CHAT INTERFACE] Message submitted:', inputValue)
    
    if (inputValue.trim() && !isLoading) {
      console.log('✅ [CHAT INTERFACE] Valid message, sending to parent')
      onSendMessage(inputValue.trim())
      setInputValue('')
    } else {
      console.log('❌ [CHAT INTERFACE] Invalid submission - empty or loading')
    }
  }

  /**
   * Handle input changes
   */
  const handleInputChange = (e) => {
    setInputValue(e.target.value)
  }

  /**
   * Handle back button click
   */
  const handleBack = () => {
    console.log('⬅️ [CHAT INTERFACE] Back button clicked')
    onBack()
  }

  /**
   * Format timestamp for display
   */
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className="chat-interface">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-title">
          <Bot size={20} />
          <span>SLATE Assistant</span>
        </div>
      </div>

      {/* Messages Container */}
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
                {message.sender === 'user' ? (
                  <User size={16} />
                ) : (
                  <Bot size={16} />
                )}
              </div>
              <div className="message-content">
                <div className="message-bubble">
                  <p>{message.text}</p>
                </div>
                <div className="message-time">
                  {formatTime(message.timestamp)}
                </div>
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

      {/* Input Form */}
      <div className="input-container">
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-wrapper">
            <input
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              placeholder="Type your message..."
              className="message-input"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="send-button"
              disabled={!inputValue.trim() || isLoading}
            >
              <Send size={18} />
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ChatInterface

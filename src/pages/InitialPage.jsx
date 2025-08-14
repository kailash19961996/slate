import { useState } from 'react'
import { motion } from 'framer-motion'
import { Bot, Sparkles, Zap, TrendingUp, Shield, ArrowRight } from 'lucide-react'
import './InitialPage.css'

const InitialPage = ({ onSendMessage }) => {
  const [inputValue, setInputValue] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim())
      setInputValue('')
    }
  }

  const handleQuickAction = (message) => {
    onSendMessage(message)
  }

  const quickActions = [
    {
      icon: <Shield className="w-5 h-5" />,
      title: "Connect Wallet",
      description: "Connect your TRON wallet to get started",
      action: "I want to connect my wallet"
    },
    {
      icon: <TrendingUp className="w-5 h-5" />,
      title: "Check Prices",
      description: "Get latest crypto prices and market data",
      action: "Show me TRX price and market overview"
    },
    {
      icon: <Zap className="w-5 h-5" />,
      title: "DeFi Opportunities",
      description: "Explore yield farming and lending",
      action: "What DeFi opportunities are available on TRON?"
    },
    {
      icon: <Bot className="w-5 h-5" />,
      title: "Learn Blockchain",
      description: "Understand blockchain concepts",
      action: "Explain how blockchain wallets work"
    }
  ]

  return (
    <div className="initial-page">
      <div className="initial-container">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="hero-section"
        >
          <div className="hero-icon">
            <motion.div
              animate={{ 
                rotate: [0, 10, -10, 0],
                scale: [1, 1.05, 1]
              }}
              transition={{ 
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <Bot className="w-16 h-16" />
            </motion.div>
          </div>
          
          <h1 className="hero-title">
            Welcome to <span className="gradient-text">SLATE</span>
          </h1>
          
          <p className="hero-subtitle">
            Your AI-powered blockchain assistant for TRON ecosystem operations
          </p>
          
          <div className="feature-badges">
            <motion.div 
              className="feature-badge"
              whileHover={{ scale: 1.05 }}
            >
              <Sparkles className="w-4 h-4" />
              <span>AI-Powered</span>
            </motion.div>
            <motion.div 
              className="feature-badge"
              whileHover={{ scale: 1.05 }}
            >
              <Shield className="w-4 h-4" />
              <span>Secure</span>
            </motion.div>
            <motion.div 
              className="feature-badge"
              whileHover={{ scale: 1.05 }}
            >
              <Zap className="w-4 h-4" />
              <span>Fast</span>
            </motion.div>
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="quick-actions"
        >
          <h2 className="section-title">Get Started</h2>
          <div className="actions-grid">
            {quickActions.map((action, index) => (
              <motion.button
                key={index}
                className="action-card"
                onClick={() => handleQuickAction(action.action)}
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ 
                  duration: 0.5, 
                  delay: 0.3 + (index * 0.1) 
                }}
              >
                <div className="action-icon">
                  {action.icon}
                </div>
                <div className="action-content">
                  <h3 className="action-title">{action.title}</h3>
                  <p className="action-description">{action.description}</p>
                </div>
                <ArrowRight className="action-arrow w-4 h-4" />
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Chat Input */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="chat-section"
        >
          <h2 className="section-title">Or Ask Me Anything</h2>
          <form onSubmit={handleSubmit} className="initial-form">
            <div className="input-container">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask about TRON, DeFi, wallets, or anything blockchain related..."
                className="initial-input"
              />
              <motion.button
                type="submit"
                disabled={!inputValue.trim()}
                className="submit-btn"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <ArrowRight className="w-5 h-5" />
              </motion.button>
            </div>
          </form>
        </motion.div>

        {/* Info Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="info-section"
        >
          <div className="info-cards">
            <div className="info-card">
              <Shield className="w-6 h-6 text-blue-400" />
              <div>
                <h4>Secure & Private</h4>
                <p>Never shares your private keys. Only uses public addresses.</p>
              </div>
            </div>
            <div className="info-card">
              <Bot className="w-6 h-6 text-green-400" />
              <div>
                <h4>AI-Powered</h4>
                <p>Advanced AI agent with blockchain expertise and real-time data.</p>
              </div>
            </div>
            <div className="info-card">
              <Zap className="w-6 h-6 text-yellow-400" />
              <div>
                <h4>TRON Ecosystem</h4>
                <p>Specialized for TRON, JustLend, JustSwap, and DeFi operations.</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default InitialPage

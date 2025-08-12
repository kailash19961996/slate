import { useState } from 'react'
import { motion } from 'framer-motion'
import { Send, Zap, TrendingUp, BarChart3 } from 'lucide-react'
import './InitialScreen.css'

const InitialScreen = ({ onSendMessage }) => {
  const [inputValue, setInputValue] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim())
      setInputValue('')
    }
  }

  const suggestions = [
    {
      icon: <TrendingUp className="w-5 h-5" />,
      text: "Show me Bitcoin price trends",
      color: "from-orange-500 to-yellow-500"
    },
    {
      icon: <BarChart3 className="w-5 h-5" />,
      text: "Analyze Ethereum DeFi metrics",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: <Zap className="w-5 h-5" />,
      text: "Market overview and top movers",
      color: "from-green-500 to-emerald-500"
    }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="initial-screen"
    >
      <div className="content-container">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="header"
        >
          <div className="logo">
            <div className="logo-icon">
              <Zap className="w-6 h-6" />
            </div>
            <h1>Slate</h1>
          </div>
          <p className="subtitle">
            Minimal crypto workspace — black & white, focused
          </p>
        </motion.div>

        <motion.form
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          onSubmit={handleSubmit}
          className="input-form"
        >
          <div className="input-shell">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask me about crypto markets, prices, DeFi, or any blockchain data..."
              className="main-input"
              autoFocus
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="send-button"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </motion.form>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="suggestions ticker"
        >
          <div className="ticker-viewport">
            <div className="ticker-track">
              {[...suggestions, ...suggestions].map((suggestion, index) => (
                <button
                  key={`s-${index}`}
                  onClick={() => onSendMessage(suggestion.text)}
                  className="suggestion-card"
                >
                  <div className={`suggestion-icon bg-gradient-to-r ${suggestion.color}`}>
                    {suggestion.icon}
                  </div>
                  <span>{suggestion.text}</span>
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 1 }}
          className="features"
        >
          <div className="feature-item">
            <div className="feature-dot"></div>
            <span>Real-time market data</span>
          </div>
          <div className="feature-item">
            <div className="feature-dot"></div>
            <span>Advanced analytics</span>
          </div>
          <div className="feature-item">
            <div className="feature-dot"></div>
            <span>DeFi protocol insights</span>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default InitialScreen
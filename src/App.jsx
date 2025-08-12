import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ChatInterface from './components/ChatInterface'
import FunctionPanel from './components/FunctionPanel'
import InitialScreen from './components/InitialScreen'
import useWebSocket from './hooks/useWebSocket'
import './App.css'

function App() {
  const [isActive, setIsActive] = useState(false)
  const [messages, setMessages] = useState([])
  const [activeFunctions, setActiveFunctions] = useState([])
  
  // WebSocket connection
  const { isConnected, lastMessage, sendMessage } = useWebSocket('ws://localhost:8000/ws')

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'ai_response':
          const aiMessage = {
            id: Date.now(),
            text: lastMessage.data.message,
            timestamp: new Date(lastMessage.data.timestamp),
            sender: 'ai'
          }
          setMessages(prev => [...prev, aiMessage])
          break
          
        case 'function_call':
          setActiveFunctions(prev => [...prev, {
            id: lastMessage.data.id,
            type: lastMessage.data.type,
            data: lastMessage.data.data
          }])
          break
          
        case 'price_update':
          // Handle real-time price updates
          console.log('Price update:', lastMessage.data)
          break
      }
    }
  }, [lastMessage])

  const handleSendMessage = (message) => {
    if (!isActive) {
      setIsActive(true)
    }
    
    const newMessage = {
      id: Date.now(),
      text: message,
      timestamp: new Date(),
      sender: 'user'
    }
    
    setMessages(prev => [...prev, newMessage])
    
    // Send message to backend via WebSocket
    if (isConnected) {
      sendMessage({ message })
    } else {
      // Fallback to mock response if WebSocket is not connected
      setTimeout(() => {
        const aiResponse = {
          id: Date.now() + 1,
          text: generateAIResponse(message),
          timestamp: new Date(),
          sender: 'ai'
        }
        setMessages(prev => [...prev, aiResponse])
        
        // Trigger function calls based on message content
        triggerFunctionCalls(message)
      }, 1000)
    }
  }

  const generateAIResponse = (userMessage) => {
    const lowerMessage = userMessage.toLowerCase()
    
    if (lowerMessage.includes('bitcoin') || lowerMessage.includes('btc')) {
      return "I'm analyzing Bitcoin data for you. Let me pull the latest price charts and market information."
    } else if (lowerMessage.includes('ethereum') || lowerMessage.includes('eth')) {
      return "Fetching Ethereum analytics and on-chain metrics. I'll show you the current trends and DeFi data."
    } else if (lowerMessage.includes('market') || lowerMessage.includes('price')) {
      return "Getting real-time market data across all major cryptocurrencies. I'll display the top movers and market sentiment."
    } else if (lowerMessage.includes('defi') || lowerMessage.includes('yield')) {
      return "Analyzing DeFi protocols and yield farming opportunities. Let me show you the best rates and risks."
    } else {
      return "I'm processing your request and gathering relevant crypto data. The information will appear on the right panel."
    }
  }

  const triggerFunctionCalls = (message) => {
    const lowerMessage = message.toLowerCase()
    
    setTimeout(() => {
      if (lowerMessage.includes('bitcoin') || lowerMessage.includes('btc')) {
        setActiveFunctions(prev => [...prev, {
          id: Date.now(),
          type: 'price_chart',
          data: {
            symbol: 'BTC',
            price: 43250.89,
            change: 2.34,
            volume: '28.5B'
          }
        }])
      }
      
      if (lowerMessage.includes('ethereum') || lowerMessage.includes('eth')) {
        setActiveFunctions(prev => [...prev, {
          id: Date.now() + 1,
          type: 'defi_metrics',
          data: {
            symbol: 'ETH',
            tvl: '48.2B',
            gasPrice: 25,
            stakingRate: 4.2
          }
        }])
      }
      
      if (lowerMessage.includes('market')) {
        setActiveFunctions(prev => [...prev, {
          id: Date.now() + 2,
          type: 'market_overview',
          data: {
            totalCap: '1.68T',
            dominance: { BTC: 42.3, ETH: 18.7 },
            fearGreed: 65
          }
        }])
      }
    }, 1500)
  }

  return (
    <div className="app">
      <AnimatePresence mode="wait">
        {!isActive ? (
          <InitialScreen key="initial" onSendMessage={handleSendMessage} />
        ) : (
          <motion.div
            key="split"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="split-screen"
          >
            <div className="chat-side">
              <ChatInterface
                messages={messages}
                onSendMessage={handleSendMessage}
                isConnected={isConnected}
              />
            </div>
            
            <motion.div
              initial={{ x: 50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="function-side"
            >
              <FunctionPanel
                functions={activeFunctions}
                onClearFunction={(id) => {
                  setActiveFunctions(prev => prev.filter(f => f.id !== id))
                }}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
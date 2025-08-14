import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ChatInterface from '../components/ChatInterface'
import FunctionPanel from '../components/FunctionPanel'
import useWebSocket from '../hooks/useWebSocket'
import './ChatPage.css'

const ChatPage = ({ initialMessage, onBack }) => {
  const [messages, setMessages] = useState([])
  const [activeFunctions, setActiveFunctions] = useState([])
  const [walletConnected, setWalletConnected] = useState(false)
  const [walletInfo, setWalletInfo] = useState(null)
  const [pendingInput, setPendingInput] = useState(null)
  
  // WebSocket connection
  const { isConnected, lastMessage, sendMessage } = useWebSocket('ws://localhost:8000/ws')

  // Initialize with message if provided
  useEffect(() => {
    if (initialMessage) {
      handleSendMessage(initialMessage)
    }
  }, [initialMessage])

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'ai_response':
          const aiMessage = {
            id: Date.now(),
            text: lastMessage.data.message,
            timestamp: new Date(lastMessage.data.timestamp),
            sender: 'ai',
            needsUserInput: lastMessage.data.needs_user_input,
            userInputPrompt: lastMessage.data.user_input_prompt
          }
          setMessages(prev => [...prev, aiMessage])
          
          // Handle pending input requests
          if (lastMessage.data.needs_user_input) {
            setPendingInput({
              type: 'wallet_address', // or other types
              prompt: lastMessage.data.user_input_prompt
            })
          } else {
            setPendingInput(null)
          }
          break
          
        case 'function_call':
          handleFunctionCall(lastMessage.data)
          break
          
        case 'wallet_connected':
          setWalletConnected(true)
          setWalletInfo(lastMessage.data.data)
          setPendingInput(null)
          break
          
        case 'price_update':
          // Handle real-time price updates
          console.log('Price update:', lastMessage.data)
          break
      }
    }
  }, [lastMessage])

  const handleFunctionCall = (functionData) => {
    const newFunction = {
      id: functionData.id || Date.now(),
      type: functionData.type,
      data: functionData.data
    }
    
    setActiveFunctions(prev => [...prev, newFunction])
  }

  const handleSendMessage = (message) => {
    // Check if this is a response to pending input
    if (pendingInput && pendingInput.type === 'wallet_address') {
      // Handle wallet address input
      handleWalletAddressInput(message)
      return
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
      sendMessage({ 
        type: 'chat',
        message: message 
      })
    } else {
      // Fallback to mock response if WebSocket is not connected
      setTimeout(() => {
        const aiResponse = {
          id: Date.now() + 1,
          text: generateMockResponse(message),
          timestamp: new Date(),
          sender: 'ai'
        }
        setMessages(prev => [...prev, aiResponse])
        
        // Trigger mock function calls
        triggerMockFunctionCalls(message)
      }, 1000)
    }
  }

  const handleWalletAddressInput = (address) => {
    // Add user message
    const userMessage = {
      id: Date.now(),
      text: address,
      timestamp: new Date(),
      sender: 'user'
    }
    setMessages(prev => [...prev, userMessage])
    
    // Send wallet address to backend
    if (isConnected) {
      sendMessage({ 
        type: 'wallet_address',
        wallet_address: address 
      })
    } else {
      // Mock wallet connection
      setTimeout(() => {
        setWalletConnected(true)
        setWalletInfo({
          address: address,
          formatted_address: `${address.slice(0, 6)}...${address.slice(-4)}`,
          status: 'connected'
        })
        setPendingInput(null)
        
        // Add confirmation message
        const confirmMessage = {
          id: Date.now() + 1,
          text: `Great! I've connected to your wallet ${address.slice(0, 6)}...${address.slice(-4)}. Let me fetch your balance and information.`,
          timestamp: new Date(),
          sender: 'ai'
        }
        setMessages(prev => [...prev, confirmMessage])
        
        // Mock wallet info function call
        handleFunctionCall({
          type: 'wallet_info',
          data: {
            address: address,
            balance: '1,234.56 TRX',
            usd_value: '$85.42',
            tokens: [
              { symbol: 'USDT', balance: '500.00', value: '$500.00' },
              { symbol: 'JST', balance: '1,000.00', value: '$25.30' }
            ]
          }
        })
      }, 1000)
    }
  }

  const generateMockResponse = (userMessage) => {
    const lowerMessage = userMessage.toLowerCase()
    
    if (lowerMessage.includes('wallet') && lowerMessage.includes('connect')) {
      return "I'd be happy to help you connect your wallet! Please provide your TRON wallet address (starts with 'T', 34 characters). I only need your public address - never share private keys or seed phrases."
    } else if (lowerMessage.includes('bitcoin') || lowerMessage.includes('btc')) {
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

  const triggerMockFunctionCalls = (message) => {
    const lowerMessage = message.toLowerCase()
    
    setTimeout(() => {
      if (lowerMessage.includes('bitcoin') || lowerMessage.includes('btc')) {
        handleFunctionCall({
          type: 'price_chart',
          data: {
            symbol: 'BTC',
            price: 43250.89,
            change: 2.34,
            volume: '28.5B',
            chart_data: generateMockChartData()
          }
        })
      }
      
      if (lowerMessage.includes('ethereum') || lowerMessage.includes('eth')) {
        handleFunctionCall({
          type: 'defi_metrics',
          data: {
            symbol: 'ETH',
            tvl: '48.2B',
            gasPrice: 25,
            stakingRate: 4.2
          }
        })
      }
      
      if (lowerMessage.includes('market')) {
        handleFunctionCall({
          type: 'market_overview',
          data: {
            totalCap: '1.68T',
            dominance: { BTC: 42.3, ETH: 18.7 },
            fearGreed: 65
          }
        })
      }

      if (lowerMessage.includes('wallet') && lowerMessage.includes('connect')) {
        setPendingInput({
          type: 'wallet_address',
          prompt: 'Please provide your TRON wallet address:'
        })
      }
    }, 1500)
  }

  const generateMockChartData = () => {
    const data = []
    const basePrice = 43000
    for (let i = 0; i < 24; i++) {
      data.push({
        timestamp: new Date(Date.now() - (24 - i) * 60 * 60 * 1000).toISOString(),
        price: basePrice + (Math.random() - 0.5) * 2000,
        volume: Math.random() * 1000000
      })
    }
    return data
  }

  const clearFunction = (id) => {
    setActiveFunctions(prev => prev.filter(f => f.id !== id))
  }

  const clearAllFunctions = () => {
    setActiveFunctions([])
  }

  return (
    <div className="chat-page">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="chat-layout"
      >
        {/* Left Side - Chat Interface */}
        <motion.div
          initial={{ x: -50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="chat-side"
        >
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            walletConnected={walletConnected}
            walletInfo={walletInfo}
            pendingInput={pendingInput}
            onBack={onBack}
          />
        </motion.div>
        
        {/* Right Side - Function Panel */}
        <motion.div
          initial={{ x: 50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="function-side"
        >
          <FunctionPanel
            functions={activeFunctions}
            onClearFunction={clearFunction}
            onClearAll={clearAllFunctions}
            walletConnected={walletConnected}
            walletInfo={walletInfo}
          />
        </motion.div>
      </motion.div>
    </div>
  )
}

export default ChatPage

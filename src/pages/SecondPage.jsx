/**
 * SecondPage.jsx - Split Screen Chat Interface
 * ==========================================
 * 
 * Split screen layout featuring:
 * - Left side: ChatInterface (50% width)
 * - Right side: FunctionPanel (50% width)
 * 
 * Component Architecture:
 * 1. ChatInterface - Handles user chat interactions with backend
 * 2. FunctionPanel - Displays dynamic widgets based on backend responses
 * 
 * State Management:
 * - Manages chat messages
 * - Handles widget display logic
 * - Coordinates backend communication
 */

import { useState, useEffect } from 'react'
import ChatInterface from '../components/ChatInterface'
import FunctionPanel from '../components/FunctionPanel'
import './SecondPage.css'

const SecondPage = ({ initialMessage, onBack }) => {
  console.log('💬 [SECOND PAGE] SecondPage component rendering')
  console.log('📨 [SECOND PAGE] Initial message:', initialMessage)
  
  // Chat state management
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  
  // Widget state management
  const [currentWidget, setCurrentWidget] = useState('idle') // 'idle', 'thinking', 'wallet'
  const [walletData, setWalletData] = useState(null)
  const [isThinking, setIsThinking] = useState(false)

  /**
   * Initialize chat with the initial message from FirstPage
   */
  useEffect(() => {
    if (initialMessage) {
      console.log('🚀 [SECOND PAGE] Initializing chat with message:', initialMessage)
      
      // Add user message
      const userMessage = {
        id: Date.now(),
        text: initialMessage,
        sender: 'user',
        timestamp: new Date()
      }
      
      setMessages([userMessage])
      handleSendToBackend(initialMessage)
    }
  }, [initialMessage])

  /**
   * Handle sending messages to real backend
   * Connects to FastAPI backend with LangGraph agent
   */
  const handleSendToBackend = async (message) => {
    console.log('🔄 [SECOND PAGE] Starting thinking animation and backend call')
    
    // Start thinking animation
    setIsThinking(true)
    setIsLoading(true)
    setCurrentWidget('thinking')

    try {
      const backendUrl = 'http://localhost:8000'
      console.log('📡 [SECOND PAGE] Connecting to backend at:', backendUrl)
      
      // Send message to chat endpoint
      const chatResponse = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: `session_${Date.now()}`
        })
      })
      
      if (!chatResponse.ok) {
        throw new Error(`Backend request failed: ${chatResponse.status}`)
      }
      
      const chatData = await chatResponse.json()
      console.log('📨 [SECOND PAGE] Backend response:', chatData)
      console.log('⏱️ [SECOND PAGE] Thinking time:', chatData.thinking_time)
      
      // Add AI response from backend
      const aiMessage = {
        id: Date.now() + 1,
        text: chatData.reply || "I received your message!",
        sender: 'ai',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, aiMessage])
      
      // Handle function calls from backend
      let hasWalletCall = false
      if (chatData.function_calls && chatData.function_calls.length > 0) {
        console.log('🛠️ [SECOND PAGE] Processing function calls:', chatData.function_calls)
        
        for (const functionCall of chatData.function_calls) {
            if (functionCall.type === 'wallet_connection_request') {
                console.log('💳 [SECOND PAGE] Wallet connection request detected')
                try {
                  const { connectTronLinkNile, readTrxBalance } = await import('../utils/tronlink');
                  const { address, nodeHost, network } = await connectTronLinkNile();
                  const balance = await readTrxBalance(address);
              
                  // send success to backend
                  await fetch('http://localhost:8000/api/wallet/connected', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      session_id: `session_${Date.now()}`,
                      address,
                      network,
                      node_host: nodeHost
                    })
                  });
              
                  setWalletData({
                    address,
                    balance,
                    formatted_address: `${address.slice(0, 6)}...${address.slice(-4)}`,
                    status: 'connected'
                  });
                  setCurrentWidget('wallet');
              
                } catch (err) {
                  console.error("❌ TronLink connect failed:", err);
                  const errorMsg = err?.message || String(err);
              
                  // send error to backend
                  await fetch('http://localhost:8000/api/wallet/error', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      session_id: `session_${Date.now()}`,
                      error: errorMsg
                    })
                  });
              
                  // optionally show in chat
                  setMessages(prev => [...prev, {
                    id: Date.now(),
                    text: `❌ Wallet connection failed: ${errorMsg}`,
                    sender: 'ai',
                    timestamp: new Date()
                  }]);
              
                  setCurrentWidget('idle');
                }
              }              
        }
      }
      
      // If no function calls, return to idle
      if (!hasWalletCall) {
        setCurrentWidget('idle')
      }
      
      console.log('✅ [SECOND PAGE] Backend response processed successfully')
      
    } catch (error) {
      console.error('❌ [SECOND PAGE] Backend connection error:', error)
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        text: "🔌 Backend is not connected. Please make sure the SLATE backend server is running on localhost:8000",
        sender: 'ai',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorMessage])
      setCurrentWidget('idle')
      
    } finally {
      setIsThinking(false)
      setIsLoading(false)
    }
  }

  /**
   * Handle new message submission from ChatInterface
   */
  const handleNewMessage = (message) => {
    console.log('📝 [SECOND PAGE] New message from chat interface:', message)
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      text: message,
      sender: 'user',
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    handleSendToBackend(message)
  }

  /**
   * Handle widget state changes
   */
  const handleWidgetChange = (newWidget) => {
    console.log('🎛️ [SECOND PAGE] Widget changed to:', newWidget)
    setCurrentWidget(newWidget)
  }

  return (
    <div className="second-page">
      <div className="split-container">
        {/* Left Split - Chat Interface */}
        <div className="left-split">
          <ChatInterface
            messages={messages}
            onSendMessage={handleNewMessage}
            isLoading={isThinking}
          />
        </div>
        
        {/* Right Split - Function Panel */}
        <div className="right-split">
          <FunctionPanel
            currentWidget={currentWidget}
            walletData={walletData}
            isLoading={isThinking}
            onWidgetChange={setCurrentWidget}
          />
        </div>
      </div>
    </div>
  )
}

export default SecondPage

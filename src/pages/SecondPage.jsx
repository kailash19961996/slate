/**
 * SecondPage.jsx - Split Screen Chat Interface
 */

import { useEffect, useRef, useState } from 'react'
import ChatInterface from '../components/ChatInterface'
import FunctionPanel from '../components/FunctionPanel'
import './SecondPage.css'

import { handleWalletInfoRequest } from '../functions/wallet_info_request'
import { handleJustLendListMarkets, handleJustLendMarketDetail, handleJustLendUserPosition } from '../functions/justlend_handlers'

const API_BASE = 'http://localhost:8000'

const SecondPage = ({ initialMessage }) => {
  console.log('💬 [SECOND PAGE] render; initialMessage =', initialMessage)

  // Chat state
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isThinking, setIsThinking] = useState(false)

  // Widgets
  const [currentWidget, setCurrentWidget] = useState('idle') // 'idle' | 'thinking' | 'wallet' | 'justlend'
  const [widgetBeforeThinking, setWidgetBeforeThinking] = useState('idle') // Track widget before thinking to restore after
  const [walletData, setWalletData] = useState(null)
  const [justLendData, setJustLendData] = useState(null)

  // Session
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const initialSentRef = useRef(false)

  // Kickoff from FirstPage, once
  useEffect(() => {
    if (initialMessage && !initialSentRef.current) {
      console.log('🚀 [SECOND PAGE] bootstrap send:', initialMessage)
      const userMessage = { id: Date.now(), text: initialMessage, sender: 'user', timestamp: new Date() }
      setMessages([userMessage])
      handleSendToBackend(initialMessage)
      initialSentRef.current = true
    }
  }, [initialMessage])

  // Single round-trip to backend
  const handleSendToBackend = async (message) => {
    console.log('🔄 [SECOND PAGE] sending to backend:', { message, sessionId })
    setIsThinking(true); setIsLoading(true)
    
    // Save current widget before switching to thinking
    setWidgetBeforeThinking(currentWidget)
    setCurrentWidget('thinking')

    try {
      const chatResponse = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId })
      })
      if (!chatResponse.ok) throw new Error(`Backend request failed: ${chatResponse.status}`)

      const chatData = await chatResponse.json()
      console.log('📬 [SECOND PAGE] /api/chat response:', chatData)

      // Natural language reply
      setMessages(prev => [...prev, { id: Date.now()+1, text: chatData.reply || 'Okay.', sender: 'ai', timestamp: new Date() }])

      let usedTool = false

      if (Array.isArray(chatData.function_calls) && chatData.function_calls.length > 0) {
        console.log('🛠️ [SECOND PAGE] function_calls:', chatData.function_calls)

        for (const fc of chatData.function_calls) {
          const type = fc?.type
          console.log('➡️ [SECOND PAGE] dispatch tool:', type, fc)

          if (type === 'wallet_info_request') {
            // Clear stale widgets/data right before a new wallet flow
            setWalletData(null)
            setCurrentWidget('thinking')

            await handleWalletInfoRequest({
              setMessages,
              setWalletData,
              setCurrentWidget,
              sessionId,
              API_BASE
            })
            usedTool = true
            continue
          }

          if (type === 'trustlender_list_markets') {
            await handleJustLendListMarkets({ fc, setMessages, setCurrentWidget, setJustLendData })
            usedTool = true
            continue
          }

          if (type === 'trustlender_market_detail') {
            await handleJustLendMarketDetail({ fc, setMessages, setCurrentWidget, setJustLendData })
            usedTool = true
            continue
          }

          if (type === 'trustlender_user_position') {
            await handleJustLendUserPosition({ fc, setMessages, setCurrentWidget, setJustLendData })
            usedTool = true
            continue
          }

          console.warn('⚠️ [SECOND PAGE] unknown function call (ignored):', type)
        }
      } else {
        console.log('ℹ️ [SECOND PAGE] no function_calls in this response')
      }

      if (!usedTool) {
        // Restore widget that was active before thinking started
        setCurrentWidget(widgetBeforeThinking)
      }
      console.log('✅ [SECOND PAGE] round-trip complete')
    } catch (error) {
      console.error('❌ [SECOND PAGE] backend round-trip failed:', error)
      setMessages(prev => [...prev, {
        id: Date.now()+2,
        text: '🔌 Backend is not connected. Make sure it runs on http://localhost:8000',
        sender: 'ai',
        timestamp: new Date()
      }])
      // Restore widget that was active before thinking started
      setCurrentWidget(widgetBeforeThinking)
    } finally {
      setIsThinking(false); setIsLoading(false)
    }
  }

  const handleNewMessage = (message) => {
    console.log('📝 [SECOND PAGE] user said:', message)
    setMessages(prev => [...prev, { id: Date.now(), text: message, sender: 'user', timestamp: new Date() }])
    handleSendToBackend(message)
  }

  return (
    <div className="second-page">
      <div className="split-container">
        {/* Left: Chat */}
        <div className="left-split">
          <ChatInterface messages={messages} onSendMessage={handleNewMessage} isLoading={isThinking} />
        </div>

        {/* Right: Widgets */}
        <div className="right-split">
          <FunctionPanel
            currentWidget={currentWidget}
            walletData={walletData}
            justLendData={justLendData}
            isLoading={isThinking}
            onWidgetChange={setCurrentWidget}
          />
        </div>
      </div>
    </div>
  )
}

export default SecondPage

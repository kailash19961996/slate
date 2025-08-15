/**
 * SecondPage.jsx - Split Screen Chat Interface
 * ===========================================
 *
 * Responsibilities:
 * - Render split view: Chat (left) + FunctionPanel (right)
 * - Manage chat state and session
 * - POST user messages to backend and render assistant replies
 * - Dispatch backend function_calls to a dedicated handler
 *
 * Important:
 * - Only the unified tool call is supported now: { type: 'wallet_info_request' }
 * - Legacy tool calls ('wallet_connection_request', 'wallet_details_request') removed
 * - The actual wallet flow (TronLink connect + snapshot + backend callbacks)
 *   lives in: src/functions/wallet_info_request.jsx
 */

import { useEffect, useRef, useState } from 'react'
import ChatInterface from '../components/ChatInterface'
import FunctionPanel from '../components/FunctionPanel'
import './SecondPage.css'

// 👉 Import the unified wallet handler (no utils folder)
import { handleWalletInfoRequest } from '../functions/wallet_info_request'
import { handleJustLendListMarkets, handleJustLendMarketDetail, handleJustLendUserPosition } from '../functions/justlend_handlers'


const API_BASE = 'http://localhost:8000'

const SecondPage = ({ initialMessage }) => {
  console.log('💬 [SECOND PAGE] Component rendering')
  console.log('📨 [SECOND PAGE] Initial message prop:', initialMessage)

  // ---------------- Chat state ----------------
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isThinking, setIsThinking] = useState(false)

  // ---------------- Widget / Panel state ----------------
  // currentWidget: 'idle' | 'thinking' | 'wallet'
  const [currentWidget, setCurrentWidget] = useState('idle')
  const [walletData, setWalletData] = useState(null)

  // ---------------- Session ----------------
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const initialSentRef = useRef(false) // prevent duplicate initial send

  const [justLendData, setJustLendData] = useState(null)

  // ============================================================================
  // Bootstrap: send the FirstPage initial message on first mount
  // ============================================================================
  useEffect(() => {
    if (initialMessage && !initialSentRef.current) {
      console.log('🚀 [SECOND PAGE] Bootstrapping with initial user message:', initialMessage)

      const userMessage = {
        id: Date.now(),
        text: initialMessage,
        sender: 'user',
        timestamp: new Date()
      }

      setMessages([userMessage])
      handleSendToBackend(initialMessage)
      initialSentRef.current = true
    }
  }, [initialMessage])

  // ============================================================================
  // Core: send message to backend, render reply, obey function_calls
  // ============================================================================
  const handleSendToBackend = async (message) => {
    console.log('🔄 [SECOND PAGE] Begin backend round-trip for message:', message)

    // UX: show "thinking" on the right panel + disable send
    setIsThinking(true)
    setIsLoading(true)
    setCurrentWidget('thinking')

    try {
      console.log('📡 [SECOND PAGE] POST /api/chat', { message, sessionId })
      const chatResponse = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId })
      })

      if (!chatResponse.ok) {
        throw new Error(`Backend request failed with status ${chatResponse.status}`)
      }

      const chatData = await chatResponse.json()
      console.log('📬 [SECOND PAGE] /api/chat response:', chatData)

      // 1) Always render the assistant's natural language reply
      const aiMessage = {
        id: Date.now() + 1,
        text: chatData.reply || 'Okay.',
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])

      // 2) Dispatch any function calls returned by backend
      let usedTool = false

      if (Array.isArray(chatData.function_calls) && chatData.function_calls.length > 0) {
        console.log('🛠️ [SECOND PAGE] function_calls to process:', chatData.function_calls)

        for (const fc of chatData.function_calls) {
          const type = fc?.type
          console.log('➡️ [SECOND PAGE] Dispatching function call type:', type)

          // ✅ Unified flow only: wallet_info_request
          if (type === 'wallet_info_request') {
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

          // If something unknown appears, log and ignore (keeps UI stable)
          console.warn('⚠️ [SECOND PAGE] Unknown function call type (ignored):', type)
        }
      } else {
        console.log('ℹ️ [SECOND PAGE] No function_calls in this response.')
      }

      // 3) If no tool ran, return the right panel to idle
      if (!usedTool) {
        setCurrentWidget('idle')
      }

      console.log('✅ [SECOND PAGE] Backend response handled successfully')
    } catch (error) {
      console.error('❌ [SECOND PAGE] Backend round-trip failed:', error)

      // Friendly user-facing error bubble
      const errorMessage = {
        id: Date.now() + 2,
        text: '🔌 Backend is not connected. Please ensure the SLATE backend server is running on http://localhost:8000',
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

  // ============================================================================
  // ChatInterface -> new outgoing user message
  // ============================================================================
  const handleNewMessage = (message) => {
    console.log('📝 [SECOND PAGE] User submitted message:', message)

    const userMessage = {
      id: Date.now(),
      text: message,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    handleSendToBackend(message)
  }

  // ============================================================================
  // Render
  // ============================================================================
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

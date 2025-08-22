/**
 * SecondPage.jsx - Main Chat Interface
 * ====================================
 * 
 * FEATURES:
 * - Split-screen layout: chat on left, widgets on right
 * - Simplified tool execution: 4 main tools only
 * - No template messages - all responses via LLM summarizer
 * - Thinking widget with delays for better UX
 * - Memory-aware conversation handling
 * 
 * TOOLS SUPPORTED:
 * - wallet_connect: TronLink connection workflow
 * - wallet_check: Balance and connection status
 * - justlend_markets: Market data display
 * - justlend_market_detail: Specific market info
 */

import { useEffect, useRef, useState } from 'react'
import ChatInterface from '../components/ChatInterface'
import FunctionPanel from '../components/FunctionPanel'
import './SecondPage.css'

import {
  handleJustLendListMarkets,
  handleJustLendMarketDetail,
  handleJustLendUserPosition
} from '../functions/justlend_handlers'

// New wallet tools
import {
  checkTronLinkPresence,
  connectWalletIfNeeded,
  fetchBalanceFlow
} from '../functions/wallet_tools'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const SecondPage = ({ initialMessage }) => {
  console.log('💬 [SECOND PAGE] render; initialMessage =', initialMessage)

  // Chat state
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isThinking, setIsThinking] = useState(false)

  // Widgets
  const [currentWidget, setCurrentWidget] = useState('idle') // 'idle' | 'thinking' | 'wallet' | 'justlend'
  const [widgetBeforeThinking, setWidgetBeforeThinking] = useState('idle')
  const [justLendData, setJustLendData] = useState(null)
  const [walletData, setWalletData] = useState(null) // Temporary display only - cleared on page refresh

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

  // ---- New helper: notify backend about a tool result (for Summarizer) ----
  async function postToolResult(result) {
    try {
      console.log('📡 [SECOND PAGE] POST /api/tools/report', result)
      await fetch(`${API_BASE}/api/tools/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, result })
      })
    } catch (e) {
      console.warn('⚠️ [SECOND PAGE] report failed (non-fatal):', e)
    }
  }

  // ---- Main round-trip to backend ----
  const handleSendToBackend = async (message) => {
    console.log('🔄 [SECOND PAGE] sending to backend:', { message, sessionId })
    setIsThinking(true); setIsLoading(true)

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

      // Show the natural-language reply (if any) from backend
      if (chatData.reply) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          text: chatData.reply,
          sender: 'ai',
          timestamp: new Date()
        }])
      }

      // Apply widget decision from backend
      if (chatData.widget) {
        console.log('🎨 [SECOND PAGE] Backend widget decision:', chatData.widget)
        const widgetType = chatData.widget.type
        const widgetData = chatData.widget.data

        if (widgetType === 'wallet' && widgetData) {
          setWalletData(widgetData)
          setCurrentWidget('wallet')
        } else if (widgetType === 'justlend' && widgetData) {
          setJustLendData(widgetData)
          setCurrentWidget('justlend')
        } else if (widgetType === 'idle') {
          setCurrentWidget('idle')
        }
      } else {
        // If backend doesn't provide a widget decision, revert to idle
        setCurrentWidget('idle')
      }

      let usedTool = false
      let finalResult = null
      let finalTool = null

      if (Array.isArray(chatData.function_calls) && chatData.function_calls.length > 0) {
        console.log('🛠️ [SECOND PAGE] function_calls:', chatData.function_calls)

        for (let i = 0; i < chatData.function_calls.length; i++) {
          const fc = chatData.function_calls[i]
          const isLastTool = i === chatData.function_calls.length - 1
          const type = fc?.type
          console.log(`➡️ [SECOND PAGE] dispatch tool ${i+1}/${chatData.function_calls.length}:`, type, fc)
          
          // Skip tools that were already executed by backend
          // Widget decisions are now handled by backend in chatData.widget
          if (fc?.executed === "backend") {
            console.log('⏩ [SECOND PAGE] Skipping backend-executed tool:', type, '(widget handled by backend)')
            continue
          }
          
          usedTool = true

          // ---- Wallet Tools (6-tool system) ----
          if (type === 'wallet_check_tronlink') {
            try {
              const result = await checkTronLinkPresence()
              await postToolResult(result)
              // Store result for potential final summarization
              finalResult = result
              finalTool = 'wallet_check_tronlink'
              // Only summarize if this is the last tool
              if (isLastTool) {
                await askBackendToSummarize('wallet_check_tronlink', result)
              }
            } catch (err) {
              const fail = { tool: 'wallet_check_tronlink', ok: false, error: err?.message || String(err) }
              finalResult = fail
              finalTool = 'wallet_check_tronlink'
              if (isLastTool) {
                await askBackendToSummarize('wallet_check_tronlink', fail)
              }
            }
            continue
          }

          if (type === 'wallet_connect') {
            try {
              const result = await connectWalletIfNeeded()
              await postToolResult(result)
              // Widget will be set by summarizer response
              // Store result - wallet_connect is more important than wallet_check_tronlink
              finalResult = result
              finalTool = 'wallet_connect'
              // Only summarize if this is the last tool
              if (isLastTool) {
                await askBackendToSummarize('wallet_connect', result)
              }
            } catch (err) {
              const fail = { tool: 'wallet_connect', ok: false, error: err?.message || String(err) }
              await postToolResult(fail)
              finalResult = fail
              finalTool = 'wallet_connect'
              if (isLastTool) {
                await askBackendToSummarize('wallet_connect', fail)
              }
            }
            continue
          }

          if (type === 'wallet_fetch_balance') {
            try {
              const result = await fetchBalanceFlow()
              await postToolResult(result)
              // Widget will be set by summarizer response
              // Store result - wallet_fetch_balance has the most complete info
              finalResult = result
              finalTool = 'wallet_fetch_balance'
              // Only summarize if this is the last tool
              if (isLastTool) {
                await askBackendToSummarize('wallet_fetch_balance', result)
              }
            } catch (err) {
              const fail = { tool: 'wallet_fetch_balance', ok: false, error: err?.message || String(err) }
              finalResult = fail
              finalTool = 'wallet_fetch_balance'
              if (isLastTool) {
                await askBackendToSummarize('wallet_fetch_balance', fail)
              }
            }
            continue
          }

          // ---- Legacy wallet_info_request removed ----
          if (type === 'wallet_info_request') {
            console.warn('⚠️ [SECOND PAGE] Legacy wallet_info_request detected')
            continue
          }

          // ---- JustLend tools ----
          // JustLend tools are handled by backend and should be skipped
          if (type === 'trustlender_list_markets' || 
              type === 'trustlender_market_detail' || 
              type === 'trustlender_user_position') {
            console.log('⚠️ [SECOND PAGE] JustLend tool should have been skipped - backend handles these')
            continue
          }

          console.warn('⚠️ [SECOND PAGE] unknown function call (ignored):', type)
        }
      } else {
        console.log('ℹ️ [SECOND PAGE] no function_calls in this response')
      }

      // Ensure thinking widget stays visible for at least a brief moment
      // Widget decisions are now handled by backend responses
      // No need to revert - backend decides the final widget state
      console.log('✅ [SECOND PAGE] round-trip complete')
    } catch (error) {
      console.error('❌ [SECOND PAGE] backend round-trip failed:', error)
      // Summarize the error through the LLM instead of template message
      await askBackendToSummarize('system_error', { 
        error: 'Backend connection failed', 
        details: error.message,
        suggestion: 'Make sure backend runs on http://localhost:8000'
      })
      // Widget decisions handled by askBackendToSummarize response
    } finally {
      setIsThinking(false); setIsLoading(false)
    }
  }

  // Ask backend to run the Summarizer over the latest tool result
  async function askBackendToSummarize(toolName, result) {
    try {
      console.log('🧠 [SECOND PAGE] POST /api/chat/summarize', { toolName, result })
      const res = await fetch(`${API_BASE}/api/chat/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, tool: toolName, result })
      })
      if (!res.ok) throw new Error(`Summarize failed ${res.status}`)
      const data = await res.json()
      if (data.reply) {
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          text: data.reply,
          sender: 'ai',
          timestamp: new Date()
        }])
      }

      // Apply widget decision from summarizer (now the authoritative source)
      if (data.widget) {
        console.log('🎨 [SECOND PAGE] Summarizer widget decision:', data.widget)
        const widgetType = data.widget.type
        const widgetData = data.widget.data

        if (widgetType === 'wallet' && widgetData) {
          setWalletData(widgetData)
          setCurrentWidget('wallet')
        } else if (widgetType === 'justlend' && widgetData) {
          setJustLendData(widgetData)
          setCurrentWidget('justlend')
        } else if (widgetType === 'idle') {
          setCurrentWidget('idle')
        }
      } else {
        // If no widget decision from summarizer, revert to idle
        setCurrentWidget('idle')
      }
    } catch (e) {
      console.warn('⚠️ [SECOND PAGE] summarize failed (non-fatal):', e)
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
            justLendData={justLendData}
            walletData={walletData}
            isLoading={isThinking}
          />
        </div>
      </div>
    </div>
  )
}

export default SecondPage

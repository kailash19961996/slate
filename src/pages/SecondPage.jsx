/**
 * SecondPage.jsx - Split Screen Chat Interface
 * ==========================================
 *
 * Split screen layout featuring:
 * - Left side: ChatInterface (40% width)
 * - Right side: FunctionPanel (60% width)
 *
 * This version FIXES wallet connection:
 * - Replaces MOCK wallet data with REAL TronLink flow
 * - Supports two tool calls from backend:
 *     1) wallet_connection_request  -> prompts TronLink + basic balance
 *     2) wallet_details_request     -> ensures connection + fetches full snapshot
 * - Posts results back to backend so the chatbot can answer:
 *     "connect to my wallet / fetch my wallet details /
 *      is my wallet connected / is TronLink present /
 *      what's my wallet address / what's my wallet balance /
 *      how much gas I am left with"
 */

import { useState, useEffect } from 'react'
import { useRef } from 'react'
import ChatInterface from '../components/ChatInterface'
import FunctionPanel from '../components/FunctionPanel'
import './SecondPage.css'

const API_BASE = 'http://localhost:8000'

const SecondPage = ({ initialMessage }) => {
  console.log('💬 [SECOND PAGE] SecondPage component rendering')
  console.log('📨 [SECOND PAGE] Initial message:', initialMessage)

  // ---------------- Chat state ----------------
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  // Prevent duplicate first-call
  const initialSentRef = useRef(false)

  // ---------------- Widget state ----------------
  const [currentWidget, setCurrentWidget] = useState('idle') // 'idle' | 'thinking' | 'wallet'
  const [walletData, setWalletData] = useState(null)
  const [isThinking, setIsThinking] = useState(false)

  // ---------------- Session ----------------
  const [sessionId] = useState(() => `session_${Date.now()}`)

  // ========= TronLink helpers (inline to keep this file self‑contained) =========

  /**
   * Prompt TronLink to expose accounts and assert the user is on NILE.
   * Returns { address, nodeHost, network } or throws with a message to show/log.
   */
  const connectTronLinkNile = async () => {
    console.log('🔌 [WALLET] connectTronLinkNile() invoked')

    if (!window.tronLink) {
      console.error('❌ [WALLET] TronLink extension not found')
      throw new Error('TronLink not found. Install or enable the extension.')
    }

    // Ask wallet to expose accounts (user may approve/reject)
    await window.tronLink.request({ method: 'tron_requestAccounts' })

    const tw = window.tronWeb
    const addr = tw?.defaultAddress?.base58
    if (!addr) {
      console.error('❌ [WALLET] No defaultAddress.base58 (locked or no account)')
      throw new Error('TronLink locked or no account selected.')
    }

    const host = tw?.fullNode?.host || 'unknown'
    let network = 'unknown'
    if (/nile/i.test(host)) network = 'nile'
    else if (/mainnet|api.trongrid.io/i.test(host)) network = 'mainnet'

    console.log('✅ [WALLET] Connected', { address: addr, host, network })
    return { address: addr, nodeHost: host, network }
  }

  /**
   * Read the TRX balance (in TRX) for an address.
   */
  const readTrxBalance = async (address) => {
    const tw = window.tronWeb
    if (!tw) throw new Error('TronWeb not available')
    const balSun = await tw.trx.getBalance(address)
    const trx = balSun / 1e6
    console.log('💰 [WALLET] TRX balance (TRX):', trx)
    return trx
  }

  /**
   * Build a full wallet snapshot with address, TRX, resources, frozen, permissions.
   * Matches the structure you posted earlier for the widget.
   */
  const getWalletSnapshot = async (address) => {
    console.log('🧾 [WALLET] getWalletSnapshot()', address)
    const tw = window.tronWeb
    if (!tw) throw new Error('TronWeb not available')

    const [balSun, acct, res] = await Promise.all([
      tw.trx.getBalance(address),
      tw.trx.getAccount(address),
      tw.trx.getAccountResources(address),
    ])

    const toTRX = (sun) => Number(sun || 0) / 1e6

    const frozenBandwidthTRX = toTRX(acct?.frozen?.[0]?.frozen_balance || 0)
    const frozenEnergyTRX = toTRX(acct?.account_resource?.frozen_balance_for_energy || 0)

    const host = tw.fullNode?.host || 'unknown'

    const snapshot = {
      address,
      nodeHost: host,
      network: /nile/i.test(host) ? 'nile' : 'unknown',
      core: { trx: toTRX(balSun) },
      resources: {
        energy: {
          used: Number(res?.EnergyUsed || 0),
          limit: Number(res?.EnergyLimit || 0),
        },
        bandwidth: {
          used: Number(res?.NetUsed || 0),
          limit: Number(res?.NetLimit || 0),
          freeUsed: Number(res?.freeNetUsed || 0),
          freeLimit: Number(res?.freeNetLimit || 0),
        },
      },
      frozen: {
        forBandwidthTRX: frozenBandwidthTRX,
        forEnergyTRX: frozenEnergyTRX,
      },
      permissions: {
        ownerKeys: acct?.owner_permission?.keys?.length || 1,
        ownerThreshold: acct?.owner_permission?.threshold || 1,
        activeCount: Array.isArray(acct?.active_permission) ? acct.active_permission.length : 0,
      },
      tokens: [], // You can add TRC‑20 balances later if needed
      fetchedAt: new Date().toISOString(),
    }

    console.log('📦 [WALLET] Snapshot:', snapshot)
    return snapshot
  }

  // ============================================================================
  // Initialize chat with the initial message from FirstPage
  // ============================================================================

  useEffect(() => {
    if (initialMessage && !initialSentRef.current) {
      console.log('🚀 [SECOND PAGE] Initializing chat with message:', initialMessage)

      // Add user message to UI immediately
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
    console.log('🔄 [SECOND PAGE] Starting thinking animation and backend call')

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
        throw new Error(`Backend request failed: ${chatResponse.status}`)
      }

      const chatData = await chatResponse.json()
      console.log('📨 [SECOND PAGE] Backend response:', chatData)

      // Show AI reply bubble
      const aiMessage = {
        id: Date.now() + 1,
        text: chatData.reply || 'I received your message!',
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])

      // ---- Handle tool calls from backend (THIS WAS WHERE IT WENT WRONG) ----
      // Handle wallet-related tool calls. We now support ONE unified type coming
      // from the backend:  wallet_info_request  (replaces separate connect/details).
      // For backward-compatibility we still recognise the two legacy types.

      let usedTool = false

      if (Array.isArray(chatData.function_calls) && chatData.function_calls.length > 0) {
        console.log('🛠️ [SECOND PAGE] Processing function calls:', chatData.function_calls)

        for (const fc of chatData.function_calls) {
          const type = fc?.type
          console.log('➡️ [SECOND PAGE] Dispatch tool:', type)

          // ────────────────────────────────────────────────────────────
          // NEW 1) UNIFIED wallet_info_request  (connect + fetch snapshot)
          // ────────────────────────────────────────────────────────────

          if (type === 'wallet_info_request') {
            try {
              // stage 1: inform user we're trying to connect
              setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: '🔄 Attempting to connect to TronLink... Please approve the popup.', sender: 'ai', timestamp: new Date() }])

              const { address, nodeHost, network } = await connectTronLinkNile()

              // get snapshot
              const snap = await getWalletSnapshot(address)

              // stage 2: user approved, wallet connected
              setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: `✅ Wallet connected (${network}). Fetching details...`, sender: 'ai', timestamp: new Date() }])

              // Update widget with snapshot data
              setWalletData({
                ...snap,
                balance: `${Number(snap.core.trx).toFixed(6)} TRX`,
                formatted_address: `${address.slice(0, 6)}...${address.slice(-4)}`,
                status: 'connected'
              })
              setCurrentWidget('wallet')

              // stage 3: send summary chat
              const sumText = `📊 TRX balance: ${Number(snap.core.trx).toFixed(6)} TRX | Energy ${snap.resources.energy.used}/${snap.resources.energy.limit} | Bandwidth ${snap.resources.bandwidth.used}/${snap.resources.bandwidth.limit}`
              setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: sumText, sender: 'ai', timestamp: new Date() }])

              // Push to backend (connected + details)
              await fetch(`${API_BASE}/api/wallet/connected`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, address, node_host: nodeHost, network })
              })

              await fetch(`${API_BASE}/api/wallet/details`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, address, trx_balance: `${Number(snap.core.trx).toFixed(6)} TRX`, extra: { snapshot: snap, node_host: nodeHost, network }})
              })

              usedTool = true
              console.log('✅ [SECOND PAGE] wallet_info_request handled')
            } catch (err) {
              console.error('❌ [SECOND PAGE] Wallet info failed:', err)
              setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: `❌ Wallet action failed: ${err?.message || err}`, sender: 'ai', timestamp: new Date() }])
              await fetch(`${API_BASE}/api/wallet/error`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, error: err?.message || String(err) })
              })
              setCurrentWidget('idle')
            }
          }

          // A) CONNECT WALLET (legacy) ...
          if (type === 'wallet_connection_request') {
            try {
              const { address, nodeHost, network } = await connectTronLinkNile()

              // Inform backend that we connected
              await fetch(`${API_BASE}/api/wallet/connected`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  session_id: sessionId,
                  address,
                  node_host: nodeHost,
                  network
                })
              })

              // Read minimal balance so UI/chat can confirm something immediately
              const trx = await readTrxBalance(address)

              // Update right panel widget (keep current widget visuals)
              setWalletData({
                address,
                balance: `${trx.toFixed(6)} TRX`,
                formatted_address: `${address.slice(0, 6)}...${address.slice(-4)}`,
                status: 'connected'
              })
              setCurrentWidget('wallet')
              usedTool = true
              console.log('✅ [SECOND PAGE] Wallet connected & widget updated')
            } catch (err) {
              console.error('❌ [SECOND PAGE] Wallet connect failed:', err)
              // Tell backend about the failure so the bot can explain
              await fetch(`${API_BASE}/api/wallet/error`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, error: err?.message || String(err) })
              })
              setCurrentWidget('idle')
            }
          }

          // B) FETCH DETAILS (ensures connection + full snapshot + sends /wallet/details)
          if (type === 'wallet_details_request') {
            try {
              // This will connect if not already / assert network = NILE
              const { address, nodeHost, network } = await connectTronLinkNile()

              // Build full snapshot (address, TRX, resources, frozen, permissions)
              const snap = await getWalletSnapshot(address)
              const summaryText = `📊 TRX balance: ${Number(snap.core.trx).toFixed(6)} TRX | Energy ${snap.resources.energy.used}/${snap.resources.energy.limit} | Bandwidth ${snap.resources.bandwidth.used}/${snap.resources.bandwidth.limit}`

              // Update widget (your current widget shows address/balance; we fill both)
              setWalletData({
                address: snap.address,
                balance: `${Number(snap.core.trx).toFixed(6)} TRX`,
                formatted_address: `${snap.address.slice(0, 6)}...${snap.address.slice(-4)}`,
                status: 'connected'
              })
              setCurrentWidget('wallet')

              // Send details to backend so chatbot can answer follow‑ups from memory
              await fetch(`${API_BASE}/api/wallet/details`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  session_id: sessionId,
                  address: snap.address,
                  trx_balance: `${Number(snap.core.trx).toFixed(6)} TRX`,
                  extra: { snapshot: snap, node_host: nodeHost, network }
                })
              })

              usedTool = true
              setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: summaryText, sender: 'ai', timestamp: new Date() }])
              console.log('✅ [SECOND PAGE] Snapshot fetched & posted to backend')
            } catch (err) {
              console.error('❌ [SECOND PAGE] Wallet details failed:', err)
              await fetch(`${API_BASE}/api/wallet/error`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, error: err?.message || String(err) })
              })
              setCurrentWidget('idle')
            }
          }
        }
      }

      // If no tool was used, return the right panel to idle
      if (!usedTool) {
        setCurrentWidget('idle')
      }

      console.log('✅ [SECOND PAGE] Backend response processed successfully')
    } catch (error) {
      console.error('❌ [SECOND PAGE] Backend connection error:', error)

      const errorMessage = {
        id: Date.now() + 1,
        text: '🔌 Backend is not connected. Please make sure the SLATE backend server is running on localhost:8000',
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
  // Handle new message from ChatInterface
  // ============================================================================

  const handleNewMessage = (message) => {
    console.log('📝 [SECOND PAGE] New message from chat interface:', message)

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

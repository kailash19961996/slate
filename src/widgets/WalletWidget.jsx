/**
 * WalletWidget.jsx - Wallet Information Display Widget
 * ===================================================
 * 
 * Displayed when wallet connection is successful:
 * - Shows wallet address (formatted)
 * - Displays balance information
 * - Shows connection status
 * - Populated by backend tool call results
 * - Only appears when wallet data is available
 */

import { Wallet, Copy, ExternalLink, CheckCircle } from 'lucide-react'
import { useState } from 'react'
import './WalletWidget.css'

const WalletWidget = ({ walletData }) => {
  console.log('💳 [WALLET WIDGET] WalletWidget component rendering')
  console.log('📊 [WALLET WIDGET] Wallet data received:', walletData)
  
  const [copied, setCopied] = useState(false)

  /**
   * Handle copying wallet address to clipboard
   */
  const handleCopyAddress = async () => {
    if (walletData?.address) {
      try {
        await navigator.clipboard.writeText(walletData.address)
        setCopied(true)
        console.log('📋 [WALLET WIDGET] Address copied to clipboard')
        
        // Reset copied state after 2 seconds
        setTimeout(() => setCopied(false), 2000)
      } catch (error) {
        console.error('❌ [WALLET WIDGET] Failed to copy address:', error)
      }
    }
  }

  /**
   * Format wallet address for display
   */
  const formatAddress = (address) => {
    if (!address) return 'N/A'
    return `${address.slice(0, 6)}...${address.slice(-4)}`
  }

  // Handle case where no wallet data is provided
  if (!walletData) {
    console.log('⚠️ [WALLET WIDGET] No wallet data provided')
    return (
      <div className="wallet-widget">
        <div className="wallet-content">
          <div className="wallet-icon">
            <Wallet size={32} />
          </div>
          <h3>No Wallet Data</h3>
          <p>Wallet information not available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="wallet-widget">
      <div className="wallet-content">
        {/* Wallet Header */}
        <div className="wallet-header">
          <div className="wallet-icon">
            <Wallet size={32} />
          </div>
          <div className="wallet-status">
            <CheckCircle size={16} />
            <span>Connected</span>
          </div>
        </div>

        {/* Wallet Address */}
        <div className="wallet-address">
          <label>Wallet Address</label>
          <div className="address-container">
            <span className="address-text">{formatAddress(walletData.address)}</span>
            <button 
              className="copy-button"
              onClick={handleCopyAddress}
              title="Copy full address"
            >
              {copied ? <CheckCircle size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>

        {/* Balance Information */}
        <div className="balance-info">
          <div className="balance-item">
            <label>TRX Balance</label>
            <span className="balance-value">{walletData.balance || '0 TRX'}</span>
          </div>
          
          {walletData.usdValue && (
            <div className="balance-item">
              <label>USD Value</label>
              <span className="balance-value">{walletData.usdValue}</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="wallet-actions">
          <button className="action-button primary">
            <ExternalLink size={16} />
            View on Explorer
          </button>
          <button className="action-button secondary">
            Refresh Balance
          </button>
        </div>

        {/* Connection Status Indicator */}
        <div className="connection-status">
          <div className="status-dot connected"></div>
          <span>Connected to TRON Network</span>
        </div>
      </div>
    </div>
  )
}

export default WalletWidget

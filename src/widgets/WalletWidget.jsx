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

import { Wallet, CheckCircle } from 'lucide-react'
import './WalletWidget.css'

const WalletWidget = ({ walletData }) => {
  console.log('💳 [WALLET WIDGET] WalletWidget component rendering')
  console.log('📊 [WALLET WIDGET] Wallet data received:', walletData)
  

  /**
   * Format wallet address for display
   */
  const formatAddress = (address) => {
    return address || 'N/A'
  }

  const handleCopyAddress = async () => {
    if (walletData?.address) {
      try {
        await navigator.clipboard.writeText(walletData.address)
        console.log('📋 [WALLET WIDGET] Address copied to clipboard')
      } catch (error) {
        console.error('❌ [WALLET WIDGET] Failed to copy address:', error)
      }
    }
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
      {/* Header with icon + status */}
      <div className="wallet-header">
        <div className="wallet-icon">
          <Wallet size={28} />
        </div>
        <div className="wallet-status">
          <CheckCircle size={14} />
          <span>Connected</span>
        </div>
      </div>

      {/* Info list */}
      <div className="wallet-info">
        {/* Address */}
        <div className="wallet-field">
          <span className="wallet-label">Address</span>
          <span className="wallet-value wallet-address">
            {formatAddress(walletData.address)}
          </span>
        </div>

        {/* TRX Balance */}
        <div className="wallet-field">
          <span className="wallet-label">TRX Balance</span>
          <span className="wallet-value">{walletData.core?.trx?.toFixed?.(6) || walletData.balance || '0'} TRX</span>
        </div>

        {/* Energy */}
        {walletData.resources?.energy && (
          <div className="wallet-field">
            <span className="wallet-label">Energy</span>
            <span className="wallet-value">{walletData.resources.energy.used}/{walletData.resources.energy.limit}</span>
          </div>
        )}

        {/* Bandwidth */}
        {walletData.resources?.bandwidth && (
          <div className="wallet-field">
            <span className="wallet-label">Bandwidth</span>
            <span className="wallet-value">{walletData.resources.bandwidth.used}/{walletData.resources.bandwidth.limit}</span>
          </div>
        )}

        {/* Network */}
        {walletData.network && (
          <div className="wallet-field">
            <span className="wallet-label">Network</span>
            <span className="wallet-value">{walletData.network}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default WalletWidget

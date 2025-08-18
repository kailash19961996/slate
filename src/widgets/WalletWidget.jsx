/**
 * WalletWidget.jsx - Wallet Tool Execution Indicator
 * =================================================
 * 
 * Displayed when wallet tools are executed:
 * - Shows that wallet operations completed
 * - No data storage per requirements
 * - Simple status indicator
 */

import { Wallet, CheckCircle, Info } from 'lucide-react'
import './WalletWidget.css'

const WalletWidget = ({ data }) => {
  console.log('💳 [WALLET WIDGET] WalletWidget component rendering with data:', data)

  // Show generic message if no data
  if (!data || !data.ok) {
    return (
      <div className="wallet-widget">
        <div className="wallet-header">
          <div className="wallet-icon">
            <Wallet size={28} />
          </div>
          <div className="wallet-status">
            <CheckCircle size={14} />
            <span>Tool Executed</span>
          </div>
        </div>
        <div className="wallet-info">
          <div className="wallet-message">
            <Info size={16} />
            <span>Wallet tool completed. Check chat for details.</span>
          </div>
          <div className="wallet-note">
            <p>💡 No wallet information is stored permanently for security.</p>
          </div>
        </div>
      </div>
    )
  }

  // Display actual wallet data temporarily
  const { summary, snapshot } = data
  
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

      {/* Wallet Data */}
      <div className="wallet-info">
        {summary && (
          <div className="wallet-field">
            <strong>Address:</strong>
            <div className="wallet-address">{summary.address}</div>
          </div>
        )}
        
        {summary && summary.network && (
          <div className="wallet-field">
            <strong>Network:</strong> {summary.network}
          </div>
        )}
        
        {snapshot && snapshot.core && (
          <div className="wallet-field">
            <strong>TRX Balance:</strong> {snapshot.core.trx?.toFixed(2) || '0'} TRX
          </div>
        )}
        
        {snapshot && snapshot.resources && (
          <div className="wallet-field">
            <strong>Energy:</strong> {snapshot.resources.energy?.used || 0} / {snapshot.resources.energy?.limit || 0}
          </div>
        )}
        
        <div className="wallet-note">
          <p>💡 Data shown temporarily - not stored permanently.</p>
        </div>
      </div>
    </div>
  )
}

export default WalletWidget

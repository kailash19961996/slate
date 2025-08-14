/**
 * FunctionPanel.jsx - Dynamic Widget Display Panel
 * ===============================================
 * 
 * Displays dynamic widgets based on chat interactions:
 * 1. IdleWidget - Default state with pulsating bubble
 * 2. ThinkingWidget - Faster pulsation with "thinking" text when AI is processing
 * 3. WalletWidget - Shows wallet information when wallet connection is successful
 * 
 * Widget switching logic:
 * - No activity: IdleWidget
 * - AI processing: ThinkingWidget
 * - Successful tool call (wallet): WalletWidget
 * - Failed tool call: Falls back to IdleWidget
 */

import IdleWidget from '../widgets/IdleWidget'
import ThinkingWidget from '../widgets/ThinkingWidget'
import WalletWidget from '../widgets/WalletWidget'
import './FunctionPanel.css'

const FunctionPanel = ({ currentWidget, walletData, isLoading, onWidgetChange }) => {
  console.log('🎛️ [FUNCTION PANEL] FunctionPanel component rendering')
  console.log('📊 [FUNCTION PANEL] Current widget:', currentWidget)
  console.log('💳 [FUNCTION PANEL] Wallet data:', walletData)
  console.log('⏳ [FUNCTION PANEL] Is loading:', isLoading)

  /**
   * Render the appropriate widget based on current state
   */
  const renderWidget = () => {
    console.log('🔄 [FUNCTION PANEL] Rendering widget:', currentWidget)
    
    switch (currentWidget) {
      case 'thinking':
        console.log('🤔 [FUNCTION PANEL] Rendering ThinkingWidget')
        return <ThinkingWidget />
        
      case 'wallet':
        console.log('💳 [FUNCTION PANEL] Rendering WalletWidget with data:', walletData)
        return <WalletWidget walletData={walletData} />
        
      case 'idle':
      default:
        console.log('😴 [FUNCTION PANEL] Rendering IdleWidget (default)')
        return <IdleWidget />
    }
  }

  return (
    <div className="function-panel">
      {/* Only Widget Container - no header/footer for minimalistic design */}
      <div className="widget-container">
        {renderWidget()}
      </div>
    </div>
  )
}

export default FunctionPanel

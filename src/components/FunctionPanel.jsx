/**
 * FunctionPanel.jsx - Dynamic Widget Display Panel
 * ===============================================
 * Renders the active widget:
 * - IdleWidget: default
 * - ThinkingWidget: when AI processing
 * - WalletWidget: after wallet_info_request
 * - JustLendWidget: after any trustlender_* tool
 */

import IdleWidget from '../widgets/IdleWidget'
import ThinkingWidget from '../widgets/ThinkingWidget'
import WalletWidget from '../widgets/WalletWidget'
import JustLendWidget from '../widgets/JustLendWidget'
import './FunctionPanel.css'

const FunctionPanel = ({ currentWidget, walletData, justLendData, isLoading, onWidgetChange }) => {
  console.log('🎛️ [FUNCTION PANEL] render')
  console.log('📊 [FUNCTION PANEL] currentWidget:', currentWidget)
  console.log('💳 [FUNCTION PANEL] walletData:', walletData)
  console.log('🏦 [FUNCTION PANEL] justLendData:', justLendData)
  console.log('⏳ [FUNCTION PANEL] isLoading:', isLoading)

  const renderWidget = () => {
    console.log('🔄 [FUNCTION PANEL] switch:', currentWidget)
    switch (currentWidget) {
      case 'thinking':
        console.log('🤔 [FUNCTION PANEL] ThinkingWidget')
        return <ThinkingWidget />
      case 'wallet':
        console.log('💳 [FUNCTION PANEL] WalletWidget')
        return <WalletWidget walletData={walletData} />
      case 'justlend':
        console.log('🏦 [FUNCTION PANEL] JustLendWidget')
        return <JustLendWidget data={justLendData} />
      case 'idle':
      default:
        console.log('😴 [FUNCTION PANEL] IdleWidget')
        return <IdleWidget />
    }
  }

  return (
    <div className="function-panel">
      <div className="widget-container">
        {renderWidget()}
      </div>
    </div>
  )
}

export default FunctionPanel

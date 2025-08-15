/**
 * ThinkingWidget.jsx - AI Thinking State Widget
 * ============================================
 * 
 * Displayed when AI is processing user requests:
 * - Faster pulsating animation than IdleWidget
 * - "Thinking..." text at the bottom
 * - More energetic visual feedback
 * - Connected to chat interface loading state
 */

import './ThinkingWidget.css'

const ThinkingWidget = () => {
  console.log('🤔 [THINKING WIDGET] ThinkingWidget component rendering')
  return (
    <div className="thinking-widget">
      <div className="thinking-dots">
        <span className="dot"></span>
        <span className="dot"></span>
        <span className="dot"></span>
      </div>
    </div>
  )
}

export default ThinkingWidget

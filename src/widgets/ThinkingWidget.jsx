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
      <div className="thinking-content">
        {/* Main pulsating bubble with faster animation */}
        <div className="thinking-bubble">
          <div className="thinking-inner">
            <div className="thinking-core"></div>
          </div>
        </div>
        
        {/* Animated thinking text */}
        <div className="thinking-text">
          <h3>Thinking</h3>
          <div className="thinking-dots">
            <span className="dot">.</span>
            <span className="dot">.</span>
            <span className="dot">.</span>
          </div>
        </div>
        
        {/* Energy rings around the bubble */}
        <div className="energy-rings">
          <div className="ring ring-1"></div>
          <div className="ring ring-2"></div>
          <div className="ring ring-3"></div>
        </div>
      </div>
    </div>
  )
}

export default ThinkingWidget

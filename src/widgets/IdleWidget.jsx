/**
 * IdleWidget.jsx - Default Idle State Widget
 * =========================================
 * 
 * Default widget displayed when no specific action is happening:
 * - Small pulsating bubble animation
 * - Minimalistic design
 * - Gentle, slow pulse rhythm
 * - Indicates system is ready and waiting
 */

import './IdleWidget.css'

const IdleWidget = () => {
  console.log('😴 [IDLE WIDGET] IdleWidget component rendering')

  return (
    <div className="idle-widget">
      <div className="idle-content">
        {/* Main pulsating bubble */}
        <div className="pulse-bubble">
          <div className="pulse-inner"></div>
        </div>
        
        {/* Status text */}
        <div className="idle-text">
          <h3>Ready</h3>
          <p>Waiting for your next request...</p>
        </div>
        
        {/* Decorative elements */}
        <div className="decorative-dots">
          <div className="dot dot-1"></div>
          <div className="dot dot-2"></div>
          <div className="dot dot-3"></div>
        </div>
      </div>
    </div>
  )
}

export default IdleWidget

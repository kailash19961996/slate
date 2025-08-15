/**
 * IdleWidget.jsx - Modern Idle State Widget
 * =========================================
 * 
 * Modern widget displaying subtle body language when idle:
 * - Gentle breathing/floating animation
 * - Organic blob shape that sways softly
 * - Mimics calm, waiting behavior
 * - Subtle eye-like elements that blink occasionally
 */

import './IdleWidget.css'

const IdleWidget = () => {
  return (
    <div className="idle-widget">
      <div className="idle-body">
        <div className="idle-core">
          <div className="idle-eye left"></div>
          <div className="idle-eye right"></div>
        </div>
        <div className="idle-aura"></div>
      </div>
    </div>
  )
}

export default IdleWidget

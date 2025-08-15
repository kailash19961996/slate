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
  return (
    <div className="idle-widget">
      <div className="idle-dots">
        <span className="dot"></span>
        <span className="dot"></span>
        <span className="dot"></span>
      </div>
    </div>
  )
}

export default IdleWidget

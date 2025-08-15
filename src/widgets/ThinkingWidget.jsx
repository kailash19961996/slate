/**
 * ThinkingWidget.jsx - Modern Thinking State Widget
 * ================================================
 * 
 * Enhanced idle-style widget for thinking state:
 * - Red colored breathing/floating animation
 * - Bigger size and faster movements
 * - Tiny stars around the core
 * - Same organic style as IdleWidget
 */

import './ThinkingWidget.css'

const ThinkingWidget = () => {
  console.log('🤔 [THINKING WIDGET] ThinkingWidget component rendering')
  return (
    <div className="thinking-widget">
      <div className="thinking-body">
        <div className="thinking-core">
          <div className="thinking-eye left"></div>
          <div className="thinking-eye right"></div>
        </div>
        <div className="thinking-aura"></div>
        <div className="thinking-stars">
          <div className="star"></div>
          <div className="star"></div>
          <div className="star"></div>
          <div className="star"></div>
          <div className="star"></div>
          <div className="star"></div>
          <div className="star"></div>
          <div className="star"></div>
        </div>
      </div>
    </div>
  )
}

export default ThinkingWidget

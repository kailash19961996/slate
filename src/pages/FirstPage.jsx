/**
 * FirstPage.jsx - Welcome Screen Component
 * =======================================
 * 
 * Simple welcome page featuring:
 * - SLATE title/branding
 * - Input field for user to type their message
 * - Clean, minimalistic design
 * - Background image from public folder
 * 
 * User Flow:
 * 1. User sees SLATE title
 * 2. User types message in input field
 * 3. User presses Enter or clicks send
 * 4. Navigation to SecondPage is triggered
 */

import { useState } from 'react'
import { Send } from 'lucide-react'
import './FirstPage.css'

const FirstPage = ({ onMessageSubmit }) => {
  console.log('🏠 [FIRST PAGE] FirstPage component rendering')
  
  const [inputValue, setInputValue] = useState('')

  /**
   * Handle form submission when user presses Enter or clicks send
   */
  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('📤 [FIRST PAGE] Form submitted with value:', inputValue)
    
    if (inputValue.trim()) {
      console.log('✅ [FIRST PAGE] Valid input, triggering navigation')
      onMessageSubmit(inputValue.trim())
    } else {
      console.log('❌ [FIRST PAGE] Empty input, ignoring submission')
    }
  }

  /**
   * Handle input value changes
   */
  const handleInputChange = (e) => {
    setInputValue(e.target.value)
    console.log('⌨️ [FIRST PAGE] Input changed:', e.target.value)
  }

  return (
    <div className="first-page">
      <div className="first-page-content">
        {/* Main Title */}
        <div className="title-section">
          <h1 className="slate-title">SLATE</h1>
        </div>

        {/* Input Section */}
        <div className="input-section">
          <form onSubmit={handleSubmit} className="message-form">
            <div className="input-wrapper">
              <input
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                placeholder="Ask me anything about blockchain, crypto, or TRON..."
                className="message-input"
                autoFocus
              />
              <button 
                type="submit" 
                className="send-button"
                disabled={!inputValue.trim()}
              >
                <Send size={20} />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default FirstPage

/**
 * App.jsx - Main Application Component
 * ===================================
 * 
 * Simple two-page application:
 * 1. FirstPage - Welcome screen with SLATE name and input
 * 2. SecondPage - Split screen with chat interface and function panel
 * 
 * Navigation Flow:
 * FirstPage -> (user types and presses enter) -> SecondPage
 */

import { useState } from 'react'
import FirstPage from './pages/FirstPage'
import SecondPage from './pages/SecondPage'
import './App.css'

function App() {
  console.log('🚀 [APP] App component rendering')
  
  // State management for page navigation
  const [currentPage, setCurrentPage] = useState('first') // 'first' or 'second'
  const [userMessage, setUserMessage] = useState('')

  /**
   * Handle user message submission from FirstPage
   * Triggers navigation to SecondPage with the user's message
   */
  const handleMessageSubmit = (message) => {
    console.log('📝 [APP] User submitted message:', message)
    setUserMessage(message)
    setCurrentPage('second')
    console.log('🔄 [APP] Navigated to second page')
  }

  /**
   * Handle back navigation to FirstPage
   * Resets state and returns to welcome screen
   */
  const handleBack = () => {
    console.log('⬅️ [APP] Navigating back to first page')
    setCurrentPage('first')
    setUserMessage('')
  }

  console.log('📊 [APP] Current page:', currentPage)

  return (
    <div className="app">
      {currentPage === 'first' ? (
        <FirstPage onMessageSubmit={handleMessageSubmit} />
      ) : (
        <SecondPage 
          initialMessage={userMessage}
          onBack={handleBack}
        />
      )}
    </div>
  )
}

export default App

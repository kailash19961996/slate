import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import InitialPage from './pages/InitialPage'
import ChatPage from './pages/ChatPage'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('initial') // 'initial' or 'chat'
  const [initialMessage, setInitialMessage] = useState(null)

  const handleSendMessage = (message) => {
    setInitialMessage(message)
    setCurrentPage('chat')
  }

  const handleBack = () => {
    setCurrentPage('initial')
    setInitialMessage(null)
  }

  return (
    <div className="app">
      <AnimatePresence mode="wait">
        {currentPage === 'initial' ? (
          <InitialPage 
            key="initial" 
            onSendMessage={handleSendMessage} 
          />
        ) : (
          <ChatPage 
            key="chat"
            initialMessage={initialMessage}
            onBack={handleBack}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
// test-backend.js - Quick test script for backend connectivity
const testBackend = async () => {
  try {
    console.log('🧪 Testing backend connectivity...')
    
    // Test health endpoint
    const healthResponse = await fetch('http://localhost:8000/health', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!healthResponse.ok) {
      throw new Error(`Health check failed: ${healthResponse.status}`)
    }
    
    const healthData = await healthResponse.json()
    console.log('✅ Health check passed:', healthData)
    
    // Test chat endpoint
    const chatResponse = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: 'Hello, test message',
        session_id: 'test_session'
      })
    })
    
    if (!chatResponse.ok) {
      throw new Error(`Chat request failed: ${chatResponse.status}`)
    }
    
    const chatData = await chatResponse.json()
    console.log('✅ Chat test passed:', chatData)
    
  } catch (error) {
    console.error('❌ Backend test failed:', error)
  }
}

// Run the test
testBackend()

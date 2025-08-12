import { useState, useEffect, useRef } from 'react'

const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = () => {
    try {
      const ws = new WebSocket(url)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        reconnectAttempts.current = 0
        setSocket(ws)
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setLastMessage(message)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        setSocket(null)
        
        // Attempt to reconnect
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1
          const timeout = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect... (${reconnectAttempts.current}/${maxReconnectAttempts})`)
            connect()
          }, timeout)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
    }
  }

  const sendMessage = (message) => {
    if (socket && isConnected) {
      try {
        socket.send(JSON.stringify(message))
      } catch (error) {
        console.error('Error sending message:', error)
      }
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (socket) {
      socket.close()
    }
    
    setSocket(null)
    setIsConnected(false)
  }

  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, [url])

  return {
    socket,
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect
  }
}

export default useWebSocket
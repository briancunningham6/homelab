import { useState, useEffect, useRef } from 'react'
import { useMissionFiles } from '../hooks/useMissions'
import type { Message } from '../types'
import '../styles/Chat.css'

interface ChatProps {
  missionId: string
}

interface StreamingMessage {
  id: string
  role: string
  content: string
  isStreaming?: boolean
  input_tokens?: number
  output_tokens?: number
  model_used?: string
}

export const Chat: React.FC<ChatProps> = ({ missionId }) => {
  const [messages, setMessages] = useState<StreamingMessage[]>([])
  const [input, setInput] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/missions/${missionId}/chat`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
      setError(null)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'user_message_saved') {
          // User message has been saved
          console.log('User message saved:', data.message_id)
        } else if (data.type === 'content') {
          // Streaming content from assistant
          setMessages((prev) => {
            const lastMsg = prev[prev.length - 1]
            if (lastMsg && lastMsg.isStreaming) {
              // Append to existing streaming message
              return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + data.content },
              ]
            } else {
              // Start new streaming message
              return [
                ...prev,
                {
                  id: 'streaming',
                  role: 'assistant',
                  content: data.content,
                  isStreaming: true,
                },
              ]
            }
          })
        } else if (data.type === 'done') {
          // Streaming complete
          setMessages((prev) => {
            const lastMsg = prev[prev.length - 1]
            if (lastMsg && lastMsg.isStreaming) {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMsg,
                  id: data.message_id,
                  isStreaming: false,
                  input_tokens: data.input_tokens,
                  output_tokens: data.output_tokens,
                  model_used: data.model,
                },
              ]
            }
            return prev
          })
          setIsStreaming(false)
        } else if (data.type === 'error') {
          setError(data.content)
          setIsStreaming(false)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onerror = (event) => {
      console.error('WebSocket error:', event)
      setError('Connection error. Please try again.')
      setIsConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
      setIsConnected(false)
    }

    wsRef.current = ws

    return () => {
      ws.close()
    }
  }, [missionId])

  // Load existing messages on mount
  useEffect(() => {
    const loadMessages = async () => {
      try {
        const response = await fetch(`/api/missions/${missionId}/messages`)
        const data = await response.json()
        setMessages(data.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          input_tokens: msg.input_tokens,
          output_tokens: msg.output_tokens,
          model_used: msg.model_used,
        })))
      } catch (err) {
        console.error('Failed to load messages:', err)
      }
    }

    loadMessages()
  }, [missionId])

  const handleSend = () => {
    if (!input.trim() || !isConnected || isStreaming) return

    const userMessage = input.trim()
    setInput('')

    // Add user message to UI immediately
    setMessages((prev) => [
      ...prev,
      {
        id: 'pending',
        role: 'user',
        content: userMessage,
      },
    ])

    // Send to WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          content: userMessage,
        })
      )
      setIsStreaming(true)
      setError(null)
    } else {
      setError('Not connected to chat server')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h3>Chat with AI Agent</h3>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {error && (
        <div className="chat-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p>No messages yet. Start a conversation with your AI agent!</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={msg.id + index} className={`message message-${msg.role}`}>
              <div className="message-header">
                <strong>{msg.role === 'user' ? 'You' : 'AI Agent'}</strong>
                {msg.model_used && (
                  <span className="message-model">{msg.model_used}</span>
                )}
              </div>
              <div className="message-content">
                {msg.content}
                {msg.isStreaming && <span className="cursor">▊</span>}
              </div>
              {msg.input_tokens && msg.output_tokens && (
                <div className="message-tokens">
                  {msg.input_tokens} in • {msg.output_tokens} out
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            isConnected
              ? 'Type your message... (Shift+Enter for new line)'
              : 'Connecting to chat server...'
          }
          disabled={!isConnected || isStreaming}
          rows={3}
        />
        <button
          className="btn btn-primary chat-send-btn"
          onClick={handleSend}
          disabled={!isConnected || isStreaming || !input.trim()}
        >
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  )
}

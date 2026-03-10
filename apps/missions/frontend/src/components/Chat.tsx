import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import { useMissionFiles } from '../hooks/useMissions'
import type { Message } from '../types'
import '../styles/Chat.css'

interface ChatProps {
  missionId: string
}

export interface ChatHandle {
  sendMessage: (text: string) => void
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

export const Chat = forwardRef<ChatHandle, ChatProps>(({ missionId }, ref) => {
  const [messages, setMessages] = useState<StreamingMessage[]>([])
  const [input, setInput] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [attachments, setAttachments] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Expose sendMessage to parent via ref
  useImperativeHandle(ref, () => ({
    sendMessage: (text: string) => {
      if (!text.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
      setMessages((prev) => [
        ...prev,
        { id: 'pending', role: 'user', content: text.trim() },
      ])
      wsRef.current.send(JSON.stringify({ type: 'message', content: text.trim(), attachments: [] }))
      setIsStreaming(true)
      setError(null)
    },
  }))

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // WebSocket connection (auto-reconnect)
  useEffect(() => {
    let cancelled = false
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/missions/${missionId}/chat`

    const connect = () => {
      if (cancelled) return

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setError(null)
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'user_message_saved') {
            console.log('User message saved:', data.message_id)
          } else if (data.type === 'content') {
            setMessages((prev) => {
              const lastMsg = prev[prev.length - 1]
              if (lastMsg && lastMsg.isStreaming) {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMsg, content: lastMsg.content + data.content },
                ]
              }
              return [
                ...prev,
                {
                  id: 'streaming',
                  role: 'assistant',
                  content: data.content,
                  isStreaming: true,
                },
              ]
            })
          } else if (data.type === 'tool_start') {
            setMessages((prev) => [
              ...prev,
              {
                id: data.tool_id,
                role: 'tool',
                tool_name: data.tool_name,
                content: '',
                isExecuting: true,
              },
            ])
          } else if (data.type === 'tool_result') {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === data.tool_id
                  ? {
                      ...msg,
                      content: JSON.stringify(data.result, null, 2),
                      isExecuting: false,
                      success: data.success,
                    }
                  : msg
              )
            )
          } else if (data.type === 'done') {
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
      }

      ws.onclose = () => {
        setIsConnected(false)
        if (!cancelled) {
          setError('Connection lost. Reconnecting...')
          reconnectTimerRef.current = window.setTimeout(connect, 1500)
        }
      }
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current)
      }
      wsRef.current?.close()
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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files) {
      setAttachments((prev) => [...prev, ...Array.from(files)])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      setAttachments((prev) => [...prev, ...Array.from(files)])
    }
  }

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index))
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    const imageItems = Array.from(e.clipboardData.items).filter(
      (item) => item.kind === 'file' && item.type.startsWith('image/')
    )
    if (imageItems.length === 0) return
    e.preventDefault()
    const files = imageItems.map((item) => item.getAsFile()).filter(Boolean) as File[]
    setAttachments((prev) => [...prev, ...files])
  }

  const handleSend = async () => {
    if ((!input.trim() && attachments.length === 0) || !isConnected || isStreaming) return

    const userMessage = input.trim()
    const filesToSend = [...attachments]

    setInput('')
    setAttachments([])

    // Add user message to UI immediately
    setMessages((prev) => [
      ...prev,
      {
        id: 'pending',
        role: 'user',
        content: userMessage + (filesToSend.length > 0 ? `\n[${filesToSend.length} file(s) attached]` : ''),
      },
    ])

    // Convert files to base64
    const fileData = await Promise.all(
      filesToSend.map(async (file) => {
        const base64 = await new Promise<string>((resolve) => {
          const reader = new FileReader()
          reader.onloadend = () => {
            const result = reader.result as string
            resolve(result.split(',')[1]) // Remove data:image/...;base64, prefix
          }
          reader.readAsDataURL(file)
        })

        return {
          filename: file.name,
          mime_type: file.type,
          size: file.size,
          data: base64,
        }
      })
    )

    // Send to WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          content: userMessage,
          attachments: fileData,
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
              {msg.role === 'tool' ? (
                <div className="tool-call">
                  <div className="tool-header">
                    🔧 {msg.tool_name}
                    {msg.isExecuting && <span className="tool-spinner">⏳</span>}
                    {!msg.isExecuting && msg.success && <span className="tool-status success">✓</span>}
                    {!msg.isExecuting && !msg.success && <span className="tool-status error">✗</span>}
                  </div>
                  {!msg.isExecuting && (
                    <div className={`tool-result ${msg.success ? 'success' : 'error'}`}>
                      <pre>{msg.content}</pre>
                    </div>
                  )}
                </div>
              ) : (
                <>
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
                </>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div
        className={`chat-input-container ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept="image/*,application/pdf,.doc,.docx,.txt"
          multiple
          style={{ display: 'none' }}
        />

        <div className="chat-input-wrapper">
          {attachments.length > 0 && (
            <div className="attachments-preview">
              {attachments.map((file, index) => (
                <div key={index} className="attachment-item">
                  <span className="attachment-name">
                    📎 {file.name}
                  </span>
                  <button
                    className="attachment-remove"
                    onClick={() => removeAttachment(index)}
                    type="button"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="input-row">
            <button
              className="btn btn-secondary attach-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={!isConnected || isStreaming}
              title="Attach file"
            >
              📎
            </button>

            <textarea
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              onPaste={handlePaste}
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
              disabled={!isConnected || isStreaming || (!input.trim() && attachments.length === 0)}
            >
              {isStreaming ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
})

Chat.displayName = 'Chat'

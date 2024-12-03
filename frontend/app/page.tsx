'use client'

import { useState, useRef, useEffect } from 'react'
import Image from 'next/image'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { API_URL } from './config'

interface Message {
  text: string
  sender: 'user' | 'bot'
  imageUrl?: string
  isStreaming?: boolean
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { text: "Hi! I'm Dream AI. I can help you analyze your dreams, create stories, write poetry, or generate dream-inspired images. Just tell me what you'd like to do!", sender: 'bot' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [backgroundImage, setBackgroundImage] = useState<string | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleStream = async (response: Response) => {
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    const botMessage: Message = { text: '', sender: 'bot', isStreaming: true }
    
    setMessages(prev => [...prev, botMessage])

    if (reader) {
      try {
        while (true) {
          const { value, done } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.text) {
                  botMessage.text = data.text
                  if (data.image_url) {
                    botMessage.imageUrl = data.image_url
                    setBackgroundImage(data.image_url)
                  }
                  setMessages(prev => 
                    prev.map((msg, i) => 
                      i === prev.length - 1 ? { ...botMessage } : msg
                    )
                  )
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e)
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
        setMessages(prev => 
          prev.map((msg, i) => 
            i === prev.length - 1 ? { ...msg, isStreaming: false } : msg
          )
        )
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    // Add user message
    setMessages(prev => [...prev, { text: input, sender: 'user' }])
    setIsLoading(true)
    setInput('') // Clear input immediately after submission

    try {
      const response = await fetch(`${API_URL}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          dream_input: input
        })
      })

      if (response.headers.get('content-type')?.includes('text/event-stream')) {
        await handleStream(response)
      } else {
        // Handle regular JSON response (for explicit image requests)
        const data = await response.json()
        if (data.status === 'success' && data.type === 'image') {
          setMessages(prev => [...prev, {
            text: "Here's your dream-inspired image:",
            sender: 'bot',
            imageUrl: data.image_url
          }])
          setBackgroundImage(data.image_url)
        } else if (data.status === 'error') {
          throw new Error(data.message)
        }
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        text: 'Sorry, I encountered an error processing your request.',
        sender: 'bot'
      }])
    }

    setIsLoading(false)
  }

  return (
    <main 
      className="min-h-screen bg-cover bg-center transition-all duration-1000"
      style={{
        backgroundImage: backgroundImage 
          ? `linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url(${backgroundImage})` 
          : 'linear-gradient(to bottom, #EBD5CF, #E2D1F9)',
        backgroundSize: 'cover',
        backgroundPosition: 'center'
      }}
    >
      <div className="container mx-auto max-w-2xl h-screen flex flex-col p-4">
        <h1 className="text-4xl font-bold text-center text-white mb-4 drop-shadow-lg">
          Dream AI
        </h1>

        <div className="flex-1 bg-black/40 backdrop-blur-md rounded-2xl shadow-lg overflow-hidden flex flex-col border border-white/10">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 shadow-lg ${
                    message.sender === 'user'
                      ? 'bg-blue-600/90 backdrop-blur-sm text-white'
                      : 'bg-white/90 backdrop-blur-sm text-black'
                  }`}
                >
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                      components={{
                        strong: (props) => (
                          <strong className="text-blue-600 dark:text-blue-400" {...props} />
                        )
                      }}
                    >
                      {message.text}
                    </ReactMarkdown>
                  </div>
                  {message.imageUrl && (
                      <Image 
                        src={message.imageUrl} 
                        alt="Generated dream image" 
                        className="rounded-lg max-w-full h-auto"
                        layout="responsive"
                        width={700}
                        height={475}
                      />
                  )}
                  {message.isStreaming && (
                    <div className="mt-1 flex space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input form */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-white/20">
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Share your dream or ask me to create a story, poem, or image..."
                className="w-full px-4 py-3 pr-24 rounded-full border border-white/40 bg-white/10 backdrop-blur-md text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent shadow-lg"
                disabled={isLoading}
              />
              <button 
                type="submit"
                disabled={!input.trim() || isLoading}
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 px-6 py-2 rounded-full transition-colors shadow-lg ${
                  input.trim() && !isLoading
                    ? 'bg-blue-600/90 hover:bg-blue-700/90 text-white backdrop-blur-sm'
                    : 'bg-white/10 text-white/50 cursor-not-allowed'
                }`}
              >
                {isLoading ? 'Thinking...' : 'Send'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}

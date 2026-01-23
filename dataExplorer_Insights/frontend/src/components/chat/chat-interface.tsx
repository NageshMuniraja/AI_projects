'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { useQueryStore } from '@/store/query-store'
import { useDatabaseStore } from '@/store/database-store'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { setResults, setInsights, setVisualizations, setCurrentQuery } = useQueryStore()
  const { selectedDatabase, connectionParams } = useDatabaseStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const queryMutation = useMutation({
    mutationFn: async (query: string) => {
      if (!selectedDatabase) {
        throw new Error('Please select a database first')
      }

      return api.processQuery({
        query,
        database_type: selectedDatabase.type,
        connection_params: connectionParams,
        use_cache: true,
      })
    },
    onSuccess: (data) => {
      setResults(data.results)
      setInsights(data.insights)
      setVisualizations(data.visualizations)
      setCurrentQuery(data.sql_query)

      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.insights?.narrative || 'Query executed successfully!',
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
      toast.success('Query executed successfully')
    },
    onError: (error: any) => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Error: ${error.message || 'Failed to process query'}`,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])
      toast.error('Failed to process query')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    queryMutation.mutate(input)
    setInput('')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Welcome to DataInsights AI
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                Ask questions about your database in natural language
              </p>
              
              <div className="space-y-2 text-left max-w-md">
                <p className="text-xs text-gray-500 font-semibold">Example queries:</p>
                <button
                  onClick={() => setInput('What are the top 10 customers by revenue?')}
                  className="block w-full text-left text-sm text-blue-600 hover:bg-blue-50 p-2 rounded"
                >
                  "What are the top 10 customers by revenue?"
                </button>
                <button
                  onClick={() => setInput('Show me sales trends for the last 6 months')}
                  className="block w-full text-left text-sm text-blue-600 hover:bg-blue-50 p-2 rounded"
                >
                  "Show me sales trends for the last 6 months"
                </button>
                <button
                  onClick={() => setInput('Which products have the highest profit margin?')}
                  className="block w-full text-left text-sm text-blue-600 hover:bg-blue-50 p-2 rounded"
                >
                  "Which products have the highest profit margin?"
                </button>
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-3xl rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {message.role === 'assistant' ? (
                <ReactMarkdown className="prose prose-sm max-w-none">
                  {message.content}
                </ReactMarkdown>
              ) : (
                <p className="text-sm">{message.content}</p>
              )}
              <p className="text-xs opacity-70 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {queryMutation.isPending && (
          <div className="flex justify-start">
            <div className="max-w-3xl rounded-lg px-4 py-2 bg-gray-100">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-gray-600">Processing your query...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4 bg-white">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your database..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={queryMutation.isPending || !selectedDatabase}
          />
          <button
            type="submit"
            disabled={queryMutation.isPending || !selectedDatabase || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {queryMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  )
}

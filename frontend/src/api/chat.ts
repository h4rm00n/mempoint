import request from '../utils/request'
import type {
  ChatCompletionRequest,
  ChatCompletionResponse,
  ChatStreamChunk
} from '../types/chat'

export const chatAPI = {
  // 发送聊天请求（非流式）
  sendMessage(data: ChatCompletionRequest) {
    return request.post<ChatCompletionResponse>('/v1/chat/completions', {
      ...data,
      stream: false
    })
  },

  // 发送聊天请求（流式）
  async sendMessageStream(
    data: ChatCompletionRequest,
    onChunk: (chunk: ChatStreamChunk) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ) {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}`
        },
        body: JSON.stringify({
          ...data,
          stream: true
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is not readable')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              onComplete()
              return
            }
            try {
              const chunk: ChatStreamChunk = JSON.parse(data)
              onChunk(chunk)
            } catch (e) {
              console.error('Failed to parse chunk:', e)
            }
          }
        }
      }

      onComplete()
    } catch (error) {
      onError(error as Error)
    }
  }
}

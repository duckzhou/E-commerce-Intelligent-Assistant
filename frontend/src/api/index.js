import axios from 'axios'

// 生产环境 API 地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 获取会话列表
export const getConversations = () => api.get('/conversations/')

// 获取单个会话详情
export const getConversation = (id) => api.get(`/conversations/${id}`)

// 删除会话
export const deleteConversation = (id) => api.delete(`/conversations/${id}`)

// 重命名会话
export const renameConversation = (id, title) => api.put(`/conversations/${id}/title`, { title })

// 置顶会话
export const pinConversation = (id) => api.put(`/conversations/${id}/pin`)

// 取消置顶会话
export const unpinConversation = (id) => api.put(`/conversations/${id}/unpin`)

// 更新消息反馈
export const updateMessageFeedback = (messageId, feedback) => api.put(`/conversations/messages/${messageId}/feedback`, { feedback: feedback || 'null' })

// 流式聊天
export const streamChat = async (query, conversationId, onChunk, onDone, onError) => {
  try {
    const token = localStorage.getItem('token')
    const headers = { 
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache'
    }
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    
    console.log('[streamChat] Request URL:', `${API_BASE_URL}/chat/stream`)
    console.log('[streamChat] Token:', token ? 'exists' : 'missing')
    console.log('[streamChat] Headers:', headers)
    
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({ query, conversation_id: conversationId })
    })

    console.log('[streamChat] Response status:', response.status)
    console.log('[streamChat] Response headers:', Object.fromEntries(response.headers.entries()))
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('[streamChat] Error response:', errorText)
      throw new Error(`HTTP error: ${response.status} - ${errorText}`)
    }

    // 检查是否支持流式读取
    if (!response.body || !response.body.getReader) {
      throw new Error('浏览器不支持流式响应，请使用现代浏览器')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let chunkCount = 0

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        console.log('[streamChat] Stream done, total chunks:', chunkCount)
        break
      }

      chunkCount++
      // 解码新接收的数据
      const text = decoder.decode(value, { stream: true })
      console.log('[streamChat] Received chunk:', text.substring(0, 100))
      buffer += text
      
      // 按行处理
      const lines = buffer.split('\n')
      // 保留最后一个可能不完整的行
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmedLine = line.trim()
        if (trimmedLine.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmedLine.slice(6))
            if (data.type === 'chunk') {
              onChunk(data.content)
            } else if (data.type === 'done') {
              console.log('[streamChat] Stream finished')
              onDone(data)
              return
            } else if (data.type === 'error') {
              onError(data.message)
              return
            }
          } catch (e) {
            console.error('Parse error:', e, trimmedLine)
          }
        }
      }
    }
    
    // 如果流结束但没有收到 done 事件，调用 onDone
    console.log('[streamChat] Stream ended without done event')
    onDone({})
  } catch (error) {
    onError(error.message)
  }
}

// 上传文档（直接请求后端）
export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch(`${API_BASE_URL}/docs/`, {
      method: 'POST',
      body: formData
      // 不设置 Content-Type，让浏览器自动设置 multipart/form-data boundary
    })
    return await response.json()
  } catch (error) {
    throw error
  }
}

// 获取文档列表
export const getDocuments = () => api.get('/docs/')

// 生成测试数据
export const seedTestData = () => api.post('/docs/seed')

export default api
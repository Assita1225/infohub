import request from '@/common/api/request'

export const getSessions = () => request.get('/chat/sessions')

export const getSession = (id) => request.get(`/chat/sessions/${id}`)

export const deleteSession = (id) => request.delete(`/chat/sessions/${id}`)

/**
 * 发送消息并以 SSE 流式接收 AI 回复。
 * 使用原生 fetch（而非 axios），因为需要 POST + ReadableStream。
 *
 * @param {Object} payload - { content, session_id?, context? }
 * @param {Object} callbacks - { onChunk({chunk, session_id}), onDone(), onError(err) }
 * @returns {Promise<void>}
 */
export async function sendMessageStream(payload, { onChunk, onDone, onError }) {
  const token = localStorage.getItem('token')

  try {
    const response = await fetch('/api/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const text = await response.text()
      try {
        const err = JSON.parse(text)
        onError(err.message || '请求失败')
      } catch {
        onError(`请求失败: ${response.status}`)
      }
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // 保留不完整的行

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6)

        if (data === '[DONE]') {
          onDone()
          return
        }

        try {
          const parsed = JSON.parse(data)
          if (parsed.error) {
            onError(parsed.error)
            return
          }
          onChunk(parsed)
        } catch {
          // 忽略无法解析的行
        }
      }
    }

    // 流正常结束但没收到 [DONE]
    onDone()
  } catch (err) {
    onError(err.message || '网络连接失败')
  }
}

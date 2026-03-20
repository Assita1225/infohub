/**
 * AI 工具箱 API —— 翻译、润色、总结，均使用 SSE 流式接收。
 * 复用 chat 模块的 SSE 模式（原生 fetch + ReadableStream）。
 */

async function toolStream(url, payload, { onChunk, onDone, onError }) {
  const token = localStorage.getItem('token')

  try {
    const response = await fetch(url, {
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
      buffer = lines.pop()

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

    onDone()
  } catch (err) {
    onError(err.message || '网络连接失败')
  }
}

export function translateStream(payload, callbacks) {
  return toolStream('/api/tools/translate', payload, callbacks)
}

export function polishStream(payload, callbacks) {
  return toolStream('/api/tools/polish', payload, callbacks)
}

export function summarizeStream(payload, callbacks) {
  return toolStream('/api/tools/summarize', payload, callbacks)
}

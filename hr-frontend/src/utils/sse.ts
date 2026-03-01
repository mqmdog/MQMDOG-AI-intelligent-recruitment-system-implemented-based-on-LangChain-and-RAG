import type { SSEEvent } from '@/types'

export interface SSECallbacks {
    onLayerInfo?: (layer: number, content: string) => void
    onToken?: (token: string) => void
    onSources?: (positions: { id: string; title: string }[]) => void
    onDone?: () => void
    onError?: (error: string) => void
}

export function createSSEConnection(
    url: string,
    token: string,
    callbacks: SSECallbacks
): { abort: () => void } {
    const abortController = new AbortController()

    const fetchSSE = async () => {
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    Authorization: `Bearer ${token}`,
                    Accept: 'text/event-stream',
                },
                signal: abortController.signal,
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const reader = response.body?.getReader()
            if (!reader) {
                throw new Error('No reader available')
            }

            const decoder = new TextDecoder()
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
                        try {
                            const event: SSEEvent = JSON.parse(data)
                            handleEvent(event, callbacks)
                        } catch (e) {
                            console.error('Failed to parse SSE event:', e)
                        }
                    }
                }
            }
        } catch (error: any) {
            if (error.name !== 'AbortError') {
                callbacks.onError?.(error.message || 'SSE connection failed')
            }
        }
    }

    fetchSSE()

    return {
        abort: () => abortController.abort(),
    }
}

function handleEvent(event: SSEEvent, callbacks: SSECallbacks) {
    switch (event.type) {
        case 'layer_info':
            if (event.layer !== undefined && event.content) {
                callbacks.onLayerInfo?.(event.layer, event.content)
            }
            break
        case 'token':
            if (event.content) {
                callbacks.onToken?.(event.content)
            }
            break
        case 'sources':
            if (event.positions) {
                callbacks.onSources?.(event.positions)
            }
            break
        case 'done':
            callbacks.onDone?.()
            break
        case 'error':
            callbacks.onError?.(event.content || 'Unknown error')
            break
    }
}

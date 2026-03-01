import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage, PositionSource } from '@/types'
import { MessageRole } from '@/types'
import { chatApi } from '@/api/chat'
import { createSSEConnection } from '@/utils/sse'
import { useAuthStore } from './auth'
import { BASE_URL } from '@/api/http'

export const useChatStore = defineStore('chat', () => {
    const sessions = ref<ChatSession[]>([])
    const currentSessionId = ref<string | null>(null)
    const messages = ref<ChatMessage[]>([])
    const isStreaming = ref(false)
    const currentLayerInfo = ref('')
    const sseConnection = ref<{ abort: () => void } | null>(null)

    async function loadSessions() {
        const response = await chatApi.getSessionList()
        sessions.value = response.sessions
    }

    async function createSession() {
        const session = await chatApi.createSession()
        sessions.value.unshift(session)
        currentSessionId.value = session.id
        messages.value = []
        return session
    }

    async function selectSession(sessionId: string) {
        currentSessionId.value = sessionId
        const response = await chatApi.getHistory(sessionId)
        messages.value = response.histories.map((h) => ({
            role: h.role,
            content: h.content,
            sources: h.retrieved_position_ids?.map((id) => ({ id, title: '' })),
        }))
    }

    async function deleteSession(sessionId: string) {
        await chatApi.deleteSession(sessionId)
        sessions.value = sessions.value.filter((s) => s.id !== sessionId)
        if (currentSessionId.value === sessionId) {
            if (sessions.value.length > 0) {
                await selectSession(sessions.value[0].id)
            } else {
                currentSessionId.value = null
                messages.value = []
            }
        }
    }

    async function sendMessage(content: string) {
        if (!currentSessionId.value || isStreaming.value) return

        const authStore = useAuthStore()
        if (!authStore.accessToken) return

        // 添加用户消息
        messages.value.push({
            role: MessageRole.USER,
            content,
        })

        // 添加助手消息占位
        messages.value.push({
            role: MessageRole.ASSISTANT,
            content: '',
            isStreaming: true,
        })

        isStreaming.value = true
        currentLayerInfo.value = ''

        const url = `${BASE_URL}/job-qa/chat/stream?session_id=${currentSessionId.value}&message=${encodeURIComponent(content)}`

        sseConnection.value = createSSEConnection(url, authStore.accessToken, {
            onLayerInfo: (layer, info) => {
                currentLayerInfo.value = info
            },
            onToken: (token) => {
                const lastMsg = messages.value[messages.value.length - 1]
                if (lastMsg && lastMsg.role === MessageRole.ASSISTANT) {
                    lastMsg.content += token
                }
            },
            onSources: (positions) => {
                const lastMsg = messages.value[messages.value.length - 1]
                if (lastMsg && lastMsg.role === MessageRole.ASSISTANT) {
                    lastMsg.sources = positions
                }
            },
            onDone: () => {
                const lastMsg = messages.value[messages.value.length - 1]
                if (lastMsg) {
                    lastMsg.isStreaming = false
                }
                isStreaming.value = false
                currentLayerInfo.value = ''
                sseConnection.value = null
            },
            onError: (error) => {
                console.error('SSE Error:', error)
                isStreaming.value = false
                currentLayerInfo.value = ''
                sseConnection.value = null
            },
        })
    }

    function abortStream() {
        if (sseConnection.value) {
            sseConnection.value.abort()
            sseConnection.value = null
            isStreaming.value = false
            currentLayerInfo.value = ''
        }
    }

    return {
        sessions,
        currentSessionId,
        messages,
        isStreaming,
        currentLayerInfo,
        loadSessions,
        createSession,
        selectSession,
        deleteSession,
        sendMessage,
        abortStream,
    }
})

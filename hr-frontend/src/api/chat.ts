import { http, BASE_URL } from './http'
import type { ChatSession, ChatHistory } from '@/types'

export const chatApi = {
    createSession(title?: string): Promise<ChatSession> {
        return http.post('/job-qa/chat/session', { title })
    },

    getSessionList(page = 1, size = 20): Promise<{ sessions: ChatSession[] }> {
        return http.get('/job-qa/chat/session/list', { params: { page, size } })
    },

    getHistory(sessionId: string): Promise<{ histories: ChatHistory[] }> {
        return http.get(`/job-qa/chat/history/${sessionId}`)
    },

    deleteSession(sessionId: string): Promise<{ message: string }> {
        return http.delete(`/job-qa/chat/session/${sessionId}`)
    },

    // 获取 SSE 流式对话的 URL
    getStreamUrl(sessionId: string, message: string, token: string): string {
        const params = new URLSearchParams({
            session_id: sessionId,
            message: message,
        })
        return `${BASE_URL}/job-qa/chat/stream?${params.toString()}`
    },
}

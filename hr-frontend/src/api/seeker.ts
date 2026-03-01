import { http } from './http'
import type { PublicPosition } from '@/types'

export const seekerApi = {
    getOpenPositions(
        page = 1,
        size = 10,
        keyword?: string
    ): Promise<{ positions: PublicPosition[]; total: number }> {
        return http.get('/job-qa/positions', {
            params: { page, size, keyword: keyword || undefined },
        })
    },

    uploadResume(file: File): Promise<{ task_id: string }> {
        const formData = new FormData()
        formData.append('file', file)
        return http.post('/job-qa/resume/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
    },

    apply(resumeId: string, positionId: string): Promise<{ task_id: string }> {
        return http.post('/job-qa/apply', {
            resume_id: resumeId,
            position_id: positionId,
        })
    },

    getApplyStatus(taskId: string): Promise<{
        task_id: string
        status: string
        result?: any
        error?: string
    }> {
        return http.get(`/job-qa/apply/status/${taskId}`)
    },
}

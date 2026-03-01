import { http } from './http'
import type { Candidate, CandidateStatus } from '@/types'

export const candidateApi = {
    getList(
        page = 1,
        size = 20,
        positionId?: string,
        status?: CandidateStatus
    ): Promise<{ candidates: Candidate[] }> {
        return http.get('/candidate/list', {
            params: { page, size, position_id: positionId, status },
        })
    },

    uploadResume(file: File): Promise<{ resume_id: string }> {
        const formData = new FormData()
        formData.append('file', file)
        return http.post('/candidate/resume/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
    },

    parseResume(resumeId: string): Promise<{ task_id: string }> {
        return http.post('/candidate/resume/parse', { resume_id: resumeId })
    },

    getParseTaskStatus(taskId: string): Promise<{ status: string; result?: any }> {
        return http.get(`/candidate/resume/parse/${taskId}`)
    },

    create(data: {
        name: string
        email?: string
        gender?: string
        birthday?: string
        phone_number?: string
        work_experience?: string
        project_experience?: string
        education_experience?: string
        skills?: string
        self_evaluation?: string
        other_information?: string
        position_id: string
        resume_id: string
    }): Promise<Candidate> {
        return http.post('/candidate/create', data)
    },
}

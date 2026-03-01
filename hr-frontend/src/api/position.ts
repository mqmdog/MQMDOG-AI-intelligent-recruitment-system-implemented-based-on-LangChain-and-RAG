import { http } from './http'
import type { Position, PositionCreateForm } from '@/types'

export const positionApi = {
    getList(page = 1, size = 20): Promise<{ positions: Position[] }> {
        return http.get('/position/list', { params: { page, size } })
    },

    create(data: PositionCreateForm): Promise<Position> {
        return http.post('/position/create', data)
    },

    delete(positionId: string): Promise<{ message: string }> {
        return http.delete(`/position/delete/${positionId}`)
    },

    // 向量化相关（管理员功能）
    embedPosition(positionId: string): Promise<{ message: string }> {
        return http.post(`/job-qa/admin/embed/position/${positionId}`)
    },

    embedAll(): Promise<{ message: string }> {
        return http.post('/job-qa/admin/embed/all')
    },
}

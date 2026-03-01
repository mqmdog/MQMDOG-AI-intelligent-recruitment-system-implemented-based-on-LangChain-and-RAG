import { http } from './http'
import type { User, LoginResponse, Department, JobSeeker, JobSeekerLoginResponse } from '@/types'

// 内部用户 API
export const userApi = {
    login(email: string, password: string): Promise<LoginResponse> {
        return http.post('/user/login', { email, password })
    },

    register(data: {
        email: string
        invite_code: string
        username: string
        realname: string
        password: string
    }): Promise<User> {
        return http.post('/user/register', data)
    },

    getDepartmentList(): Promise<{ departments: Department[] }> {
        return http.get('/user/department/list')
    },

    getUserList(page = 1, size = 20, departmentId?: string): Promise<{ users: User[] }> {
        return http.get('/user/list', { params: { page, size, department_id: departmentId } })
    },
}

// 求职者 API
export const jobSeekerApi = {
    register(data: {
        username: string
        email: string
        password: string
        phone_number?: string
    }): Promise<JobSeeker> {
        return http.post('/job-qa/register', data)
    },

    login(email: string, password: string): Promise<JobSeekerLoginResponse> {
        return http.post('/job-qa/login', { email, password })
    },

    getMe(): Promise<JobSeeker> {
        return http.get('/job-qa/me')
    },
}

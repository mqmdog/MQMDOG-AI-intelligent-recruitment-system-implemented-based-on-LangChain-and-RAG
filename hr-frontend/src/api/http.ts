import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

const BASE_URL = 'http://localhost:8000'

const http: AxiosInstance = axios.create({
    baseURL: BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// 请求拦截器
http.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const authStore = useAuthStore()
        if (authStore.accessToken) {
            config.headers.Authorization = `Bearer ${authStore.accessToken}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
http.interceptors.response.use(
    (response) => {
        return response.data
    },
    async (error) => {
        const authStore = useAuthStore()

        if (error.response?.status === 401) {
            // Token 过期，清除认证状态
            authStore.logout()
            window.location.href = '/auth/login'
        }

        return Promise.reject(error.response?.data || error)
    }
)

export { http, BASE_URL }

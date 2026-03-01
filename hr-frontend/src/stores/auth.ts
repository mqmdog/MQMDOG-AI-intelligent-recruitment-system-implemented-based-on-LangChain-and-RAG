import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, JobSeeker } from '@/types'
import { userApi, jobSeekerApi } from '@/api/user'

export type UserRole = 'job_seeker' | 'employee' | 'hr' | 'superuser'

export const useAuthStore = defineStore(
    'auth',
    () => {
        // 状态
        const accessToken = ref<string | null>(null)
        const refreshToken = ref<string | null>(null)
        const user = ref<User | null>(null)
        const jobSeeker = ref<JobSeeker | null>(null)
        const userType = ref<'internal' | 'job_seeker' | null>(null)

        // 计算属性
        const isLoggedIn = computed(() => !!accessToken.value)
        const isJobSeeker = computed(() => userType.value === 'job_seeker')
        const isInternal = computed(() => userType.value === 'internal')
        const isHR = computed(() => user.value?.is_hr || false)
        const isSuperUser = computed(() => user.value?.is_superuser || false)

        const currentRole = computed<UserRole | null>(() => {
            if (userType.value === 'job_seeker') return 'job_seeker'
            if (!user.value) return null
            if (user.value.is_superuser) return 'superuser'
            if (user.value.is_hr) return 'hr'
            return 'employee'
        })

        // 内部用户登录
        async function loginInternal(email: string, password: string) {
            const response = await userApi.login(email, password)
            accessToken.value = response.access_token
            refreshToken.value = response.refresh_token
            user.value = response.user
            userType.value = 'internal'
        }

        // 求职者登录
        async function loginJobSeeker(email: string, password: string) {
            const response = await jobSeekerApi.login(email, password)
            accessToken.value = response.access_token
            refreshToken.value = response.refresh_token
            jobSeeker.value = response.job_seeker
            userType.value = 'job_seeker'
        }

        // 登出
        function logout() {
            accessToken.value = null
            refreshToken.value = null
            user.value = null
            jobSeeker.value = null
            userType.value = null
        }

        return {
            accessToken,
            refreshToken,
            user,
            jobSeeker,
            userType,
            isLoggedIn,
            isJobSeeker,
            isInternal,
            isHR,
            isSuperUser,
            currentRole,
            loginInternal,
            loginJobSeeker,
            logout,
        }
    },
    {
        persist: true,
    }
)

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        redirect: '/auth/login',
    },
    // 认证路由
    {
        path: '/auth',
        component: () => import('@/layouts/AuthLayout.vue'),
        children: [
            {
                path: 'login',
                name: 'Login',
                component: () => import('@/views/auth/LoginView.vue'),
            },
            {
                path: 'register',
                name: 'Register',
                component: () => import('@/views/auth/RegisterView.vue'),
            },
        ],
    },
    // 求职者路由
    {
        path: '/seeker',
        component: () => import('@/layouts/SeekerLayout.vue'),
        meta: { requiresAuth: true, userType: 'job_seeker' },
        children: [
            {
                path: '',
                redirect: '/seeker/home',
            },
            {
                path: 'home',
                name: 'SeekerHome',
                component: () => import('@/views/seeker/HomeView.vue'),
            },
            {
                path: 'apply',
                name: 'SeekerApply',
                component: () => import('@/views/seeker/ApplyView.vue'),
            },
        ],
    },
    // 内部人员路由
    {
        path: '/internal',
        component: () => import('@/layouts/InternalLayout.vue'),
        meta: { requiresAuth: true, userType: 'internal' },
        children: [
            {
                path: '',
                redirect: '/internal/dashboard',
            },
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('@/views/internal/DashboardView.vue'),
            },
            {
                path: 'positions',
                name: 'Positions',
                component: () => import('@/views/internal/PositionsView.vue'),
            },
            {
                path: 'candidates',
                name: 'Candidates',
                component: () => import('@/views/internal/CandidatesView.vue'),
            },
        ],
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()

    // 已登录用户访问登录页，重定向到对应首页
    if (to.path.startsWith('/auth') && authStore.isLoggedIn) {
        if (authStore.isJobSeeker) {
            return next('/seeker/home')
        } else {
            return next('/internal/dashboard')
        }
    }

    // 需要认证的路由
    if (to.meta.requiresAuth && !authStore.isLoggedIn) {
        return next('/auth/login')
    }

    // 检查用户类型
    if (to.meta.userType === 'job_seeker' && !authStore.isJobSeeker) {
        return next('/internal/dashboard')
    }
    if (to.meta.userType === 'internal' && authStore.isJobSeeker) {
        return next('/seeker/home')
    }

    next()
})

export default router

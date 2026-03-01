// 用户相关类型
export interface User {
    id: string
    username: string
    email: string
    realname: string
    phone_number?: string
    avatar?: string
    department?: Department
    status: UserStatus
    is_hr: boolean
    is_superuser: boolean
    created_at: string
}

export interface Department {
    id: string
    name: string
    description?: string
}

export enum UserStatus {
    ACTIVE = 'ACTIVE',
    BLOCKED = 'BLOCKED',
    RESIGNED = 'RESIGNED',
}

export interface LoginResponse {
    access_token: string
    refresh_token: string
    user: User
    message?: string
}

// 求职者相关类型
export interface JobSeeker {
    id: string
    username: string
    email: string
    phone_number?: string
    status: JobSeekerStatus
    created_at: string
}

export enum JobSeekerStatus {
    ACTIVE = 'ACTIVE',
    BLOCKED = 'BLOCKED',
}

export interface JobSeekerLoginResponse {
    access_token: string
    refresh_token: string
    job_seeker: JobSeeker
    message?: string
}

// 职位相关类型
export interface Position {
    id: string
    title: string
    description?: string
    requirements?: string
    min_salary?: number
    max_salary?: number
    deadline?: string
    recruitment_count: number
    education: Education
    work_year: number
    is_open: boolean
    department?: Department
    creator?: User
    created_at: string
}

export enum Education {
    COLLEGE = '大专',
    BACHELOR = '本科',
    MASTER = '硕士',
    DOCTOR = '博士',
    UNKNOWN = '未知',
}

export interface PositionCreateForm {
    title: string
    description?: string
    requirements?: string
    min_salary?: number
    max_salary?: number
    deadline?: string
    recruitment_count?: number
    education?: Education
    work_year?: number
    department_id: string
}

// 候选人相关类型
export interface Candidate {
    id: string
    name: string
    gender: Gender
    birthday?: string
    email?: string
    phone_number?: string
    work_experience?: string
    project_experience?: string
    education_experience?: string
    skills?: string
    self_evaluation?: string
    other_information?: string
    status: CandidateStatus
    position?: Position
    resume?: Resume
    creator?: User
    ai_score?: AIScore
    created_at: string
}

export enum Gender {
    MALE = '男',
    FEMALE = '女',
    UNKNOWN = '未知',
}

export enum CandidateStatus {
    APPLICATION = '已投递',
    AI_FILTER_FAILED = 'AI筛选失败',
    AI_FILTER_PASSED = 'AI筛选成功',
    WAITING_FOR_INTERVIEW = '待面试',
    REFUSED_INTERVIEW = '拒绝面试',
    INTERVIEW_PASSED = '面试通过',
    INTERVIEW_FAILED = '面试未通过',
    HIRED = '已入职',
    REJECTED = '已拒绝',
}

export interface Resume {
    id: string
    file_path: string
    uploader?: User
    created_at: string
}

export interface AIScore {
    id: string
    work_experience_score: number
    technical_skills_score: number
    soft_skills_score: number
    educational_background_score: number
    project_experience_score: number
    overall_score: number
    summary: string
    strengths: string[]
    weaknesses: string[]
}

// 对话相关类型
export interface ChatSession {
    id: string
    title?: string
    created_at: string
    updated_at: string
}

export interface ChatHistory {
    id: string
    role: MessageRole
    content: string
    retrieved_position_ids?: string[]
    created_at: string
}

export enum MessageRole {
    USER = 'USER',
    ASSISTANT = 'ASSISTANT',
}

export interface ChatMessage {
    role: MessageRole
    content: string
    isStreaming?: boolean
    sources?: PositionSource[]
}

export interface PositionSource {
    id: string
    title: string
}

// SSE 事件类型
export interface SSEEvent {
    type: 'layer_info' | 'token' | 'sources' | 'done' | 'error'
    layer?: number
    content?: string
    positions?: PositionSource[]
}

// API 响应类型
export interface ApiResponse<T = any> {
    data: T
    message?: string
}

export interface PaginatedResponse<T> {
    items: T[]
    total: number
    page: number
    size: number
}

// 求职者投递相关类型
export interface PublicPosition {
    id: string
    title: string
    description?: string
    requirements?: string
    min_salary?: number
    max_salary?: number
    deadline?: string
    recruitment_count: number
    education: Education
    work_year: number
    department_name: string
}

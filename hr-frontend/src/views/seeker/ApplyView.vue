<template>
  <div class="apply-view">
    <div class="apply-header">
      <h2>投递简历</h2>
      <p>选择心仪职位，上传简历，AI 智能匹配评分</p>
    </div>

    <el-steps :active="currentStep" finish-status="success" align-center class="apply-steps">
      <el-step title="选择职位" />
      <el-step title="上传简历" />
      <el-step title="处理进度" />
    </el-steps>

    <div class="step-content">
      <!-- 步骤 1: 选择职位 -->
      <div v-if="currentStep === 0" class="step-select-position">
        <div class="search-bar">
          <el-input
            v-model="keyword"
            placeholder="搜索职位名称..."
            clearable
            size="large"
            @input="onSearchInput"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div v-if="loading" class="loading-container">
          <el-icon class="is-loading" :size="24"><Loading /></el-icon>
          <span>加载中...</span>
        </div>

        <div v-else-if="positions.length === 0" class="empty-container">
          <el-empty description="暂无开放职位" />
        </div>

        <div v-else class="position-grid">
          <div
            v-for="pos in positions"
            :key="pos.id"
            class="position-card"
            :class="{ selected: selectedPosition?.id === pos.id }"
            @click="selectedPosition = pos"
          >
            <div class="position-card-top">
              <h3>{{ pos.title }}</h3>
              <span class="salary">
                {{ formatSalary(pos.min_salary, pos.max_salary) }}
              </span>
            </div>
            <div class="position-card-tags">
              <el-tag size="small" type="info" effect="plain" round>{{ pos.department_name || '未分配' }}</el-tag>
              <el-tag size="small" effect="plain" round>{{ pos.education }}</el-tag>
              <el-tag size="small" effect="plain" round v-if="pos.work_year > 0">{{ pos.work_year }}年经验</el-tag>
              <el-tag size="small" effect="plain" round v-else>经验不限</el-tag>
            </div>
            <div v-if="pos.description" class="position-card-desc">
              {{ pos.description.slice(0, 100) }}{{ pos.description.length > 100 ? '...' : '' }}
            </div>
            <div class="position-card-footer">
              <span v-if="pos.deadline" class="deadline">
                截止: {{ new Date(pos.deadline).toLocaleDateString() }}
              </span>
              <el-tag v-if="selectedPosition?.id === pos.id" type="success" size="small" effect="dark" round>
                已选择
              </el-tag>
            </div>
          </div>
        </div>

        <div class="pagination-container" v-if="total > pageSize">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="loadPositions"
          />
        </div>

        <div class="step-actions">
          <el-button
            type="primary"
            size="large"
            :disabled="!selectedPosition"
            @click="currentStep = 1"
          >
            下一步：上传简历
          </el-button>
        </div>
      </div>

      <!-- 步骤 2: 上传简历 -->
      <div v-if="currentStep === 1" class="step-upload-resume">
        <div class="selected-position-summary">
          <div class="summary-label">已选职位</div>
          <div class="summary-card">
            <div class="summary-title">{{ selectedPosition?.title }}</div>
            <div class="summary-meta">
              <span>{{ selectedPosition?.department_name }}</span>
              <span class="dot">-</span>
              <span class="summary-salary">{{ formatSalary(selectedPosition?.min_salary, selectedPosition?.max_salary) }}</span>
            </div>
          </div>
        </div>

        <div class="upload-area">
          <div class="upload-label">上传简历</div>
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            class="resume-upload"
          >
            <div class="upload-inner">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <div class="upload-hint">
                支持 PDF、Word、图片格式，文件大小不超过 10MB
              </div>
            </div>
          </el-upload>
        </div>

        <div class="step-actions">
          <el-button size="large" @click="currentStep = 0">返回上一步</el-button>
          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            :disabled="!uploadFile"
            @click="submitApplication"
          >
            提交申请
          </el-button>
        </div>
      </div>

      <!-- 步骤 3: 处理进度 -->
      <div v-if="currentStep === 2" class="step-progress">
        <div v-if="taskError" class="result-container">
          <el-result icon="error" title="处理失败" :sub-title="taskError">
            <template #extra>
              <el-button type="primary" size="large" @click="resetAll">重新投递</el-button>
            </template>
          </el-result>
        </div>

        <div v-else-if="taskStatus === 'done'" class="result-container">
          <el-result icon="success" title="投递成功" sub-title="您的简历已成功投递！AI 系统已完成初步筛选，HR 将尽快与您联系。">
            <template #extra>
              <el-button type="primary" size="large" @click="resetAll">继续投递</el-button>
            </template>
          </el-result>
        </div>

        <div v-else class="progress-container">
          <h3>正在处理您的申请</h3>
          <p class="progress-hint">请耐心等待，AI 正在分析您的简历...</p>
          <el-steps :active="progressStep" direction="vertical" :space="80" class="progress-steps">
            <el-step title="解析简历内容" description="OCR 识别简历文字" />
            <el-step title="AI 提取个人信息" description="智能提取候选人信息" />
            <el-step title="创建候选人档案" description="生成候选人记录" />
            <el-step title="AI 智能匹配评分" description="与职位要求进行匹配" />
          </el-steps>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, Loading, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import type { PublicPosition } from '@/types'
import { seekerApi } from '@/api/seeker'

const currentStep = ref(0)

// 步骤 1 状态
const keyword = ref('')
const positions = ref<PublicPosition[]>([])
const selectedPosition = ref<PublicPosition | null>(null)
const loading = ref(false)
const currentPage = ref(1)
const pageSize = 10
const total = ref(0)
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 步骤 2 状态
const uploadFile = ref<File | null>(null)
const uploadRef = ref()
const submitting = ref(false)

// 步骤 3 状态
const taskId = ref<string | null>(null)
const taskStatus = ref<string | null>(null)
const taskError = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const progressStep = computed(() => {
  switch (taskStatus.value) {
    case 'pending': return 0
    case 'ocr_done': return 1
    case 'ai_extracted': return 2
    case 'candidate_created': return 3
    case 'done': return 4
    default: return 0
  }
})

onMounted(() => {
  loadPositions()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (searchTimer) clearTimeout(searchTimer)
})

function formatSalary(min?: number, max?: number): string {
  if (min && max) return `${min}k-${max}k`
  if (min) return `${min}k起`
  if (max) return `最高${max}k`
  return '面议'
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadPositions()
  }, 500)
}

async function loadPositions() {
  loading.value = true
  try {
    const res = await seekerApi.getOpenPositions(
      currentPage.value,
      pageSize,
      keyword.value || undefined,
    )
    positions.value = res.positions
    total.value = res.total
  } catch (e: any) {
    ElMessage.error(e.detail || '加载职位失败')
  } finally {
    loading.value = false
  }
}

function handleFileChange(file: UploadFile) {
  uploadFile.value = file.raw || null
}

function handleFileRemove() {
  uploadFile.value = null
}

async function submitApplication() {
  if (!uploadFile.value || !selectedPosition.value) return
  submitting.value = true
  try {
    // 1. 上传简历
    const uploadRes = await seekerApi.uploadResume(uploadFile.value)
    const resumeId = uploadRes.task_id

    // 2. 提交申请
    const applyRes = await seekerApi.apply(resumeId, selectedPosition.value.id)
    taskId.value = applyRes.task_id
    taskStatus.value = 'pending'
    taskError.value = null

    // 3. 进入步骤 3
    currentStep.value = 2
    startPolling()
  } catch (e: any) {
    ElMessage.error(e.detail || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    if (!taskId.value) return
    try {
      const res = await seekerApi.getApplyStatus(taskId.value)
      taskStatus.value = res.status
      if (res.status === 'done') {
        clearInterval(pollTimer!)
        pollTimer = null
      } else if (res.status === 'failed') {
        taskError.value = res.error || '处理失败'
        clearInterval(pollTimer!)
        pollTimer = null
      }
    } catch {
      // 忽略轮询错误
    }
  }, 2000)
}

function resetAll() {
  currentStep.value = 0
  selectedPosition.value = null
  uploadFile.value = null
  taskId.value = null
  taskStatus.value = null
  taskError.value = null
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}
</script>

<style scoped>
.apply-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow-y: auto;
}

.apply-view::-webkit-scrollbar {
  width: 6px;
}

.apply-view::-webkit-scrollbar-track {
  background: transparent;
}

.apply-view::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.apply-header {
  padding: 28px 32px 0;
  text-align: center;
}

.apply-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 600;
  color: #1d2129;
}

.apply-header p {
  font-size: 14px;
  color: #86909c;
}

.apply-steps {
  padding: 24px 60px 0;
}

.step-content {
  flex: 1;
  padding: 24px 32px 32px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

/* --- 搜索 --- */
.search-bar {
  margin-bottom: 20px;
}

.search-bar :deep(.el-input__wrapper) {
  border-radius: 10px;
}

.loading-container {
  text-align: center;
  padding: 60px 0;
  color: #86909c;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 15px;
}

.empty-container {
  padding: 40px 0;
}

/* --- 职位网格 --- */
.position-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
}

.position-card {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #e8ecf0;
  background: #fafbfc;
  cursor: pointer;
  transition: all 0.2s;
}

.position-card:hover {
  border-color: #b3d8ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.08);
  transform: translateY(-1px);
}

.position-card.selected {
  border-color: #409eff;
  background: #f0f7ff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.15);
}

.position-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.position-card-top h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.4;
}

.salary {
  font-weight: 700;
  color: #f56c6c;
  font-size: 15px;
  white-space: nowrap;
}

.position-card-tags {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.position-card-desc {
  margin-top: 12px;
  font-size: 13px;
  color: #86909c;
  line-height: 1.6;
}

.position-card-footer {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.deadline {
  font-size: 12px;
  color: #c0c4cc;
}

.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.step-actions {
  margin-top: 32px;
  display: flex;
  justify-content: center;
  gap: 16px;
}

/* --- 步骤 2 --- */
.selected-position-summary {
  margin-bottom: 28px;
}

.summary-label,
.upload-label {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.summary-card {
  padding: 16px 20px;
  border-radius: 10px;
  background: #f0f7ff;
  border: 1px solid #d4e8ff;
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.summary-meta {
  margin-top: 6px;
  display: flex;
  gap: 8px;
  color: #86909c;
  font-size: 14px;
  align-items: center;
}

.dot {
  color: #dcdfe6;
}

.summary-salary {
  color: #f56c6c;
  font-weight: 600;
}

.upload-area {
  margin-bottom: 24px;
}

.resume-upload {
  width: 100%;
}

.resume-upload :deep(.el-upload-dragger) {
  border-radius: 12px;
  border: 2px dashed #dcdfe6;
  padding: 40px 20px;
  transition: all 0.2s;
}

.resume-upload :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: #f0f7ff;
}

.upload-inner {
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 12px;
}

.upload-text {
  font-size: 15px;
  color: #4e5969;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.upload-hint {
  margin-top: 8px;
  font-size: 13px;
  color: #c0c4cc;
}

/* --- 步骤 3 --- */
.progress-container {
  text-align: center;
  padding: 20px 0;
}

.progress-container h3 {
  margin-bottom: 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
}

.progress-hint {
  color: #86909c;
  font-size: 14px;
  margin-bottom: 32px;
}

.progress-steps {
  max-width: 400px;
  margin: 0 auto;
}

.result-container {
  padding: 20px 0;
}
</style>

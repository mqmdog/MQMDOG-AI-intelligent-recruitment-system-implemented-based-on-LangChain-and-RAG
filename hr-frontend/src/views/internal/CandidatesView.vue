<template>
  <div class="candidates-view">
    <div class="page-header">
      <h2>候选人管理</h2>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="职位筛选">
          <el-select
            v-model="filters.positionId"
            placeholder="全部职位"
            clearable
            @change="loadCandidates"
          >
            <el-option
              v-for="pos in positions"
              :key="pos.id"
              :label="pos.title"
              :value="pos.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态筛选">
          <el-select
            v-model="filters.status"
            placeholder="全部状态"
            clearable
            @change="loadCandidates"
          >
            <el-option
              v-for="status in statusOptions"
              :key="status"
              :label="status"
              :value="status"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="candidates" v-loading="loading" stripe>
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="email" label="邮箱" width="180" />
      <el-table-column prop="phone_number" label="电话" width="130" />
      <el-table-column prop="position.title" label="应聘职位" width="150" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="AI 评分" width="100">
        <template #default="{ row }">
          <span v-if="row.ai_score" class="ai-score">
            {{ row.ai_score.overall_score }}/10
          </span>
          <span v-else class="no-score">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="投递时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="showDetail(row)">
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 候选人详情对话框 -->
    <el-dialog v-model="detailVisible" title="候选人详情" width="700px">
      <template v-if="currentCandidate">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="姓名">{{ currentCandidate.name }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ currentCandidate.gender }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ currentCandidate.email }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ currentCandidate.phone_number }}</el-descriptions-item>
          <el-descriptions-item label="应聘职位">{{ currentCandidate.position?.title }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentCandidate.status)">
              {{ currentCandidate.status }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentCandidate.ai_score" class="ai-score-card">
          <h4>AI 评分</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="score-item">
                <span class="label">综合评分</span>
                <el-progress
                  :percentage="currentCandidate.ai_score.overall_score * 10"
                  :stroke-width="10"
                />
              </div>
            </el-col>
            <el-col :span="8">
              <div class="score-item">
                <span class="label">工作经验</span>
                <el-progress
                  :percentage="currentCandidate.ai_score.work_experience_score * 10"
                  :stroke-width="10"
                />
              </div>
            </el-col>
            <el-col :span="8">
              <div class="score-item">
                <span class="label">技术能力</span>
                <el-progress
                  :percentage="currentCandidate.ai_score.technical_skills_score * 10"
                  :stroke-width="10"
                />
              </div>
            </el-col>
          </el-row>
          <div class="score-summary">
            <p><strong>评价：</strong>{{ currentCandidate.ai_score.summary }}</p>
            <p v-if="currentCandidate.ai_score.strengths?.length">
              <strong>优势：</strong>{{ currentCandidate.ai_score.strengths.join('、') }}
            </p>
            <p v-if="currentCandidate.ai_score.weaknesses?.length">
              <strong>不足：</strong>{{ currentCandidate.ai_score.weaknesses.join('、') }}
            </p>
          </div>
        </div>

        <div v-if="currentCandidate.work_experience" class="detail-section">
          <h4>工作经历</h4>
          <p>{{ currentCandidate.work_experience }}</p>
        </div>

        <div v-if="currentCandidate.skills" class="detail-section">
          <h4>技能</h4>
          <p>{{ currentCandidate.skills }}</p>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { Candidate, Position, CandidateStatus } from '@/types'
import { candidateApi } from '@/api/candidate'
import { positionApi } from '@/api/position'

const candidates = ref<Candidate[]>([])
const positions = ref<Position[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const currentCandidate = ref<Candidate | null>(null)

const filters = reactive({
  positionId: '',
  status: '' as CandidateStatus | '',
})

const statusOptions = [
  '已投递',
  'AI筛选失败',
  'AI筛选成功',
  '待面试',
  '拒绝面试',
  '面试通过',
  '面试未通过',
  '已入职',
  '已拒绝',
]

onMounted(async () => {
  await Promise.all([loadCandidates(), loadPositions()])
})

async function loadCandidates() {
  loading.value = true
  try {
    const res = await candidateApi.getList(
      1,
      100,
      filters.positionId || undefined,
      filters.status as CandidateStatus || undefined
    )
    candidates.value = res.candidates
  } finally {
    loading.value = false
  }
}

async function loadPositions() {
  try {
    const res = await positionApi.getList(1, 100)
    positions.value = res.positions
  } catch (error) {
    console.error('Failed to load positions:', error)
  }
}

function getStatusType(status: string): string {
  const typeMap: Record<string, string> = {
    '已投递': 'info',
    'AI筛选失败': 'danger',
    'AI筛选成功': 'success',
    '待面试': 'warning',
    '拒绝面试': 'info',
    '面试通过': 'success',
    '面试未通过': 'danger',
    '已入职': 'success',
    '已拒绝': 'info',
  }
  return typeMap[status] || 'info'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function showDetail(candidate: Candidate) {
  currentCandidate.value = candidate
  detailVisible.value = true
}
</script>

<style scoped>
.candidates-view {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.filter-card {
  margin-bottom: 20px;
}

.ai-score {
  color: #409eff;
  font-weight: bold;
}

.no-score {
  color: #909399;
}

.ai-score-card {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.ai-score-card h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.score-item {
  margin-bottom: 10px;
}

.score-item .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.score-summary {
  margin-top: 15px;
  font-size: 14px;
  color: #606266;
}

.score-summary p {
  margin: 8px 0;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.detail-section p {
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>

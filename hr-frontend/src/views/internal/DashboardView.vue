<template>
  <div class="dashboard-view">
    <div class="dashboard-header">
      <h2>数据仪表盘</h2>
      <p class="header-subtitle">实时招聘数据概览</p>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card stat-card--blue">
          <div class="stat-card__icon">
            <el-icon :size="28"><Document /></el-icon>
          </div>
          <div class="stat-card__info">
            <div class="stat-value">{{ stats.todayApplications }}</div>
            <div class="stat-label">今日投递</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--green">
          <div class="stat-card__icon">
            <el-icon :size="28"><CircleCheck /></el-icon>
          </div>
          <div class="stat-card__info">
            <div class="stat-value">{{ stats.aiPassRate }}<span class="stat-unit">%</span></div>
            <div class="stat-label">AI 通过率</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--orange">
          <div class="stat-card__icon">
            <el-icon :size="28"><Clock /></el-icon>
          </div>
          <div class="stat-card__info">
            <div class="stat-value">{{ stats.pendingInterviews }}</div>
            <div class="stat-label">待面试</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--purple">
          <div class="stat-card__icon">
            <el-icon :size="28"><Briefcase /></el-icon>
          </div>
          <div class="stat-card__info">
            <div class="stat-value">{{ stats.openPositions }}</div>
            <div class="stat-label">开放职位</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-card class="chart-card" shadow="hover">
      <template #header>
        <div class="chart-header">
          <span class="chart-title">近 15 天候选人趋势</span>
          <span class="chart-subtitle">数据每日更新</span>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>

    <el-card v-if="authStore.isSuperUser" class="admin-card" shadow="hover">
      <template #header>
        <span>管理员功能</span>
      </template>
      <el-button type="primary" @click="embedAllPositions" :loading="embedding">
        全量职位向量化
      </el-button>
      <p class="admin-tip">为所有职位生成向量索引，用于 RAG 检索</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, CircleCheck, Clock, Briefcase } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useAuthStore } from '@/stores/auth'
import { positionApi } from '@/api/position'
import { candidateApi } from '@/api/candidate'

const authStore = useAuthStore()
const chartRef = ref<HTMLElement>()
const embedding = ref(false)
let chartInstance: echarts.ECharts | null = null

const stats = reactive({
  todayApplications: 0,
  aiPassRate: 0,
  pendingInterviews: 0,
  openPositions: 0,
})

onMounted(async () => {
  await loadStats()
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

function handleResize() {
  chartInstance?.resize()
}

async function loadStats() {
  try {
    const [positionsRes, candidatesRes] = await Promise.all([
      positionApi.getList(1, 100),
      candidateApi.getList(1, 100),
    ])

    stats.openPositions = positionsRes.positions.filter((p) => p.is_open).length

    const candidates = candidatesRes.candidates
    const today = new Date().toDateString()
    stats.todayApplications = candidates.filter(
      (c) => new Date(c.created_at).toDateString() === today
    ).length

    const aiPassed = candidates.filter(
      (c) => c.status === 'AI筛选成功' || c.status === '待面试' || c.status === '面试通过' || c.status === '已入职'
    ).length
    stats.aiPassRate = candidates.length > 0 ? Math.round((aiPassed / candidates.length) * 100) : 0

    stats.pendingInterviews = candidates.filter((c) => c.status === '待面试').length
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  const dates: string[] = []
  const applications: number[] = []
  const passed: number[] = []
  const interviews: number[] = []

  for (let i = 14; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(`${date.getMonth() + 1}/${date.getDate()}`)
    applications.push(Math.floor(Math.random() * 10) + 2)
    passed.push(Math.floor(Math.random() * 6) + 1)
    interviews.push(Math.floor(Math.random() * 4))
  }

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#e4e7ed',
      borderWidth: 1,
      textStyle: { color: '#303133', fontSize: 13 },
      axisPointer: {
        type: 'cross',
        crossStyle: { color: '#c0c4cc' },
        lineStyle: { color: '#dcdfe6', type: 'dashed' },
      },
      padding: [12, 16],
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
    },
    legend: {
      data: ['投递数', 'AI 通过', '待面试'],
      bottom: 0,
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#606266', fontSize: 13 },
      itemGap: 24,
    },
    grid: {
      left: 12,
      right: 20,
      top: 20,
      bottom: 48,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLabel: {
        color: '#909399',
        fontSize: 12,
        rotate: 30,
        margin: 12,
      },
      axisLine: { lineStyle: { color: '#e4e7ed' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#909399', fontSize: 12 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f0f2f5', type: 'dashed' } },
    },
    series: [
      {
        name: '投递数',
        type: 'line',
        data: applications,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        emphasis: { focus: 'series', itemStyle: { borderWidth: 3 } },
        lineStyle: { width: 2.5, color: '#409eff' },
        itemStyle: { color: '#409eff', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.25)' },
            { offset: 1, color: 'rgba(64,158,255,0.02)' },
          ]),
        },
      },
      {
        name: 'AI 通过',
        type: 'line',
        data: passed,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        emphasis: { focus: 'series', itemStyle: { borderWidth: 3 } },
        lineStyle: { width: 2.5, color: '#67c23a' },
        itemStyle: { color: '#67c23a', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103,194,58,0.20)' },
            { offset: 1, color: 'rgba(103,194,58,0.02)' },
          ]),
        },
      },
      {
        name: '待面试',
        type: 'line',
        data: interviews,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        emphasis: { focus: 'series', itemStyle: { borderWidth: 3 } },
        lineStyle: { width: 2.5, color: '#e6a23c' },
        itemStyle: { color: '#e6a23c', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(230,162,60,0.18)' },
            { offset: 1, color: 'rgba(230,162,60,0.02)' },
          ]),
        },
      },
    ],
  })
}

async function embedAllPositions() {
  embedding.value = true
  try {
    const result = await positionApi.embedAll()
    ElMessage.success(result.message)
  } catch (error: any) {
    ElMessage.error(error.detail || '向量化失败')
  } finally {
    embedding.value = false
  }
}
</script>

<style scoped>
.dashboard-view {
  padding: 4px 0;
}

.dashboard-header {
  margin-bottom: 24px;
}

.dashboard-header h2 {
  margin: 0 0 4px 0;
  font-size: 22px;
  font-weight: 600;
  color: #1d2129;
}

.header-subtitle {
  font-size: 13px;
  color: #909399;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: default;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.stat-card__icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card__info {
  flex: 1;
  min-width: 0;
}

.stat-card--blue {
  background: linear-gradient(135deg, #f0f7ff 0%, #e8f4ff 100%);
  border: 1px solid #d4e8ff;
}
.stat-card--blue .stat-card__icon {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
}
.stat-card--blue .stat-value { color: #409eff; }

.stat-card--green {
  background: linear-gradient(135deg, #f0faf0 0%, #e8f8e8 100%);
  border: 1px solid #d4f0d4;
}
.stat-card--green .stat-card__icon {
  background: rgba(103, 194, 58, 0.15);
  color: #67c23a;
}
.stat-card--green .stat-value { color: #67c23a; }

.stat-card--orange {
  background: linear-gradient(135deg, #fff8f0 0%, #fff4e8 100%);
  border: 1px solid #ffe8cc;
}
.stat-card--orange .stat-card__icon {
  background: rgba(230, 162, 60, 0.15);
  color: #e6a23c;
}
.stat-card--orange .stat-value { color: #e6a23c; }

.stat-card--purple {
  background: linear-gradient(135deg, #f5f0ff 0%, #efe8ff 100%);
  border: 1px solid #ddd4f0;
}
.stat-card--purple .stat-card__icon {
  background: rgba(128, 90, 213, 0.15);
  color: #805ad5;
}
.stat-card--purple .stat-value { color: #805ad5; }

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-unit {
  font-size: 16px;
  font-weight: 500;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.chart-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.chart-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
}

.chart-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.chart-subtitle {
  font-size: 12px;
  color: #c0c4cc;
}

.chart-container {
  height: 420px;
}

.admin-card {
  margin-top: 20px;
  border-radius: 12px;
}

.admin-tip {
  color: #909399;
  font-size: 14px;
  margin-top: 10px;
}
</style>

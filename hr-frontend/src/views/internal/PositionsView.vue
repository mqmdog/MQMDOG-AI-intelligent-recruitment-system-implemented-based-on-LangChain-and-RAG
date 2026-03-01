<template>
  <div class="positions-view">
    <div class="page-header">
      <h2>职位管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新增职位
      </el-button>
    </div>

    <el-table :data="positions" v-loading="loading" stripe>
      <el-table-column prop="title" label="职位名称" width="180" />
      <el-table-column prop="department.name" label="部门" width="120" />
      <el-table-column label="薪资" width="140">
        <template #default="{ row }">
          {{ formatSalary(row.min_salary, row.max_salary) }}
        </template>
      </el-table-column>
      <el-table-column prop="education" label="学历" width="80" />
      <el-table-column label="工作年限" width="100">
        <template #default="{ row }">
          {{ row.work_year }}年以上
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_open ? 'success' : 'info'">
            {{ row.is_open ? '招聘中' : '已关闭' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="embedPosition(row.id)">
            向量化
          </el-button>
          <el-popconfirm
            title="确定删除该职位吗？"
            @confirm="deletePosition(row.id)"
          >
            <template #reference>
              <el-button text type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增职位对话框 -->
    <el-dialog v-model="dialogVisible" title="新增职位" width="600px">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="职位名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入职位名称" />
        </el-form-item>
        <el-form-item label="所属部门" prop="department_id">
          <el-select v-model="form.department_id" placeholder="请选择部门" style="width: 100%">
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最低薪资">
              <el-input-number v-model="form.min_salary" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最高薪资">
              <el-input-number v-model="form.max_salary" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学历要求">
              <el-select v-model="form.education" style="width: 100%">
                <el-option label="不限" value="未知" />
                <el-option label="大专" value="大专" />
                <el-option label="本科" value="本科" />
                <el-option label="硕士" value="硕士" />
                <el-option label="博士" value="博士" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工作年限">
              <el-input-number v-model="form.work_year" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="职位描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入职位描述"
          />
        </el-form-item>
        <el-form-item label="职位要求">
          <el-input
            v-model="form.requirements"
            type="textarea"
            :rows="3"
            placeholder="请输入职位要求"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createPosition" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { Position, Department } from '@/types'
import { positionApi } from '@/api/position'
import { userApi } from '@/api/user'

const positions = ref<Position[]>([])
const departments = ref<Department[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  title: '',
  department_id: '',
  min_salary: undefined as number | undefined,
  max_salary: undefined as number | undefined,
  education: '未知',
  work_year: 0,
  description: '',
  requirements: '',
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入职位名称', trigger: 'blur' }],
  department_id: [{ required: true, message: '请选择部门', trigger: 'change' }],
}

onMounted(async () => {
  await Promise.all([loadPositions(), loadDepartments()])
})

async function loadPositions() {
  loading.value = true
  try {
    const res = await positionApi.getList(1, 100)
    positions.value = res.positions
  } finally {
    loading.value = false
  }
}

async function loadDepartments() {
  try {
    const res = await userApi.getDepartmentList()
    departments.value = res.departments
  } catch (error) {
    console.error('Failed to load departments:', error)
  }
}

function formatSalary(min?: number, max?: number): string {
  if (min && max) return `${min}k-${max}k`
  if (min) return `${min}k起`
  if (max) return `最高${max}k`
  return '面议'
}

function showCreateDialog() {
  Object.assign(form, {
    title: '',
    department_id: '',
    min_salary: undefined,
    max_salary: undefined,
    education: '未知',
    work_year: 0,
    description: '',
    requirements: '',
  })
  dialogVisible.value = true
}

async function createPosition() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      await positionApi.create(form as any)
      ElMessage.success('职位创建成功')
      dialogVisible.value = false
      await loadPositions()
    } catch (error: any) {
      ElMessage.error(error.detail || '创建失败')
    } finally {
      submitting.value = false
    }
  })
}

async function deletePosition(id: string) {
  try {
    await positionApi.delete(id)
    ElMessage.success('删除成功')
    await loadPositions()
  } catch (error: any) {
    ElMessage.error(error.detail || '删除失败')
  }
}

async function embedPosition(id: string) {
  try {
    const result = await positionApi.embedPosition(id)
    ElMessage.success(result.message)
  } catch (error: any) {
    ElMessage.error(error.detail || '向量化失败')
  }
}
</script>

<style scoped>
.positions-view {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}
</style>

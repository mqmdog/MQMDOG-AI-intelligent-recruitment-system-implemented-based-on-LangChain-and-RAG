<template>
  <div class="login-view">
    <el-tabs v-model="loginType" class="login-tabs">
      <el-tab-pane label="求职者登录" name="job_seeker" />
      <el-tab-pane label="内部员工登录" name="internal" />
    </el-tabs>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      @submit.prevent="handleLogin"
    >
      <el-form-item label="邮箱" prop="email">
        <el-input
          v-model="form.email"
          placeholder="请输入邮箱"
          type="email"
        />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          placeholder="请输入密码"
          type="password"
          show-password
        />
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          native-type="submit"
          :loading="loading"
          style="width: 100%"
        >
          登录
        </el-button>
      </el-form-item>
    </el-form>

    <div class="login-footer" v-if="loginType === 'job_seeker'">
      还没有账号？
      <router-link to="/auth/register">立即注册</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const loginType = ref<'job_seeker' | 'internal'>('job_seeker')

const form = reactive({
  email: '',
  password: '',
})

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度为 6-20 位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      if (loginType.value === 'job_seeker') {
        await authStore.loginJobSeeker(form.email, form.password)
        ElMessage.success('登录成功')
        router.push('/seeker/home')
      } else {
        await authStore.loginInternal(form.email, form.password)
        ElMessage.success('登录成功')
        router.push('/internal/dashboard')
      }
    } catch (error: any) {
      ElMessage.error(error.detail || '登录失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-view {
  padding-top: 10px;
}

.login-tabs {
  margin-bottom: 20px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #909399;
}

.login-footer a {
  color: #409eff;
  text-decoration: none;
}
</style>

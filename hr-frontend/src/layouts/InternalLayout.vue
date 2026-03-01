<template>
  <div class="internal-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>HR 管理后台</h2>
      </div>

      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/internal/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>数据仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/internal/positions">
          <el-icon><Briefcase /></el-icon>
          <span>职位管理</span>
        </el-menu-item>
        <el-menu-item index="/internal/candidates">
          <el-icon><User /></el-icon>
          <span>候选人管理</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <div class="user-info">
          <el-tag v-if="authStore.isSuperUser" type="danger" size="small">超级管理员</el-tag>
          <el-tag v-else-if="authStore.isHR" type="warning" size="small">HR</el-tag>
          <span>{{ authStore.user?.realname }}</span>
        </div>
        <el-button text @click="logout">退出</el-button>
      </div>
    </aside>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataLine, Briefcase, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

function logout() {
  authStore.logout()
  router.push('/auth/login')
}
</script>

<style scoped>
.internal-layout {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  width: 220px;
  background: #304156;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
  color: white;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  color: #bfcbd9;
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-menu-item.is-active) {
  background: #263445;
  color: #409eff;
}

.sidebar-footer {
  padding: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #bfcbd9;
}

.sidebar-footer .el-button {
  color: #bfcbd9;
}

.main-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}
</style>

<template>
  <div class="seeker-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon">
            <el-icon :size="22" color="#fff"><ChatDotRound /></el-icon>
          </div>
          <h2>智能招聘助手</h2>
        </div>
      </div>

      <div class="sidebar-nav">
        <div
          class="nav-item"
          :class="{ active: route.path.startsWith('/seeker/home') }"
          @click="router.push('/seeker/home')"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </div>
        <div
          class="nav-item"
          :class="{ active: route.path.startsWith('/seeker/apply') }"
          @click="router.push('/seeker/apply')"
        >
          <el-icon><Document /></el-icon>
          <span>投递简历</span>
        </div>
      </div>

      <template v-if="route.path.startsWith('/seeker/home')">
        <div class="sidebar-section">
          <el-button class="new-chat-btn" @click="createNewChat" :loading="creating">
            <el-icon><Plus /></el-icon>
            新建对话
          </el-button>
        </div>

        <div class="sidebar-section session-section">
          <h3>历史对话</h3>
          <div class="session-list">
            <div
              v-for="session in chatStore.sessions"
              :key="session.id"
              class="session-item"
              :class="{ active: session.id === chatStore.currentSessionId }"
              @click="selectSession(session.id)"
            >
              <el-icon class="session-icon"><ChatDotRound /></el-icon>
              <span class="session-title">{{ session.title || '新对话' }}</span>
              <el-icon
                class="session-delete"
                @click.stop="confirmDeleteSession(session.id)"
              >
                <Delete />
              </el-icon>
            </div>
            <div v-if="chatStore.sessions.length === 0" class="empty-sessions">
              暂无历史对话
            </div>
          </div>
        </div>
      </template>

      <div class="sidebar-footer">
        <div class="user-info">
          <el-avatar :size="32" class="user-avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="user-name">{{ authStore.jobSeeker?.username }}</span>
        </div>
        <el-button text size="small" @click="logout" class="logout-btn">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </aside>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Plus, ChatDotRound, Document, Delete, User, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { ElMessageBox, ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const chatStore = useChatStore()
const creating = ref(false)

onMounted(async () => {
  await chatStore.loadSessions()
  if (chatStore.sessions.length > 0 && !chatStore.currentSessionId) {
    const firstSession = chatStore.sessions[0]
    if (firstSession) {
      await chatStore.selectSession(firstSession.id)
    }
  }
})

async function createNewChat() {
  creating.value = true
  try {
    await chatStore.createSession()
  } finally {
    creating.value = false
  }
}

async function selectSession(sessionId: string) {
  await chatStore.selectSession(sessionId)
}

async function confirmDeleteSession(sessionId: string) {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？删除后无法恢复。', '删除对话', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await chatStore.deleteSession(sessionId)
    ElMessage.success('对话已删除')
  } catch {
    // 用户取消
  }
}

function logout() {
  authStore.logout()
  router.push('/auth/login')
}
</script>

<style scoped>
.seeker-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: #f0f2f5;
}

/* --- 侧边栏 --- */
.sidebar {
  width: 272px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #1d2129 0%, #2a2f3a 100%);
  display: flex;
  flex-direction: column;
  color: #fff;
}

.sidebar-header {
  padding: 20px 20px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #409eff 0%, #36cfc9 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: 0.5px;
}

/* --- 导航 --- */
.sidebar-nav {
  padding: 4px 12px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.65);
  margin-bottom: 2px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.9);
}

.nav-item.active {
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

/* --- 新建对话按钮 --- */
.sidebar-section {
  padding: 12px 16px 0;
}

.new-chat-btn {
  width: 100%;
  border: 1px dashed rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.85);
  border-radius: 8px;
  height: 38px;
  font-size: 13px;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background: rgba(64, 158, 255, 0.15);
  border-color: rgba(64, 158, 255, 0.4);
  color: #409eff;
}

/* --- 会话列表 --- */
.session-section {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-top: 16px;
}

.session-section h3 {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  margin: 0 0 8px 4px;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 500;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.session-list::-webkit-scrollbar {
  width: 4px;
}

.session-list::-webkit-scrollbar-track {
  background: transparent;
}

.session-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

.session-item {
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 2px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s;
}

.session-icon {
  font-size: 14px;
  flex-shrink: 0;
  opacity: 0.5;
}

.session-title {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-delete {
  flex-shrink: 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.3);
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
  cursor: pointer;
}

.session-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.85);
}

.session-item:hover .session-delete {
  opacity: 1;
}

.session-delete:hover {
  color: #f56c6c;
}

.session-item.active {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
}

.session-item.active .session-icon {
  opacity: 1;
}

.empty-sessions {
  padding: 24px 12px;
  text-align: center;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.25);
}

/* --- 底部用户 --- */
.sidebar-footer {
  margin-top: auto;
  padding: 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.user-avatar {
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.8);
  flex-shrink: 0;
}

.user-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

.logout-btn:hover {
  color: #f56c6c;
}

/* --- 主内容区 --- */
.main-content {
  flex: 1;
  overflow: hidden;
  padding: 16px 20px 16px 16px;
}
</style>

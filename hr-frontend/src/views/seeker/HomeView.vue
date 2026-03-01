<template>
  <div class="home-view">
    <div class="chat-container">
      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef">
        <div v-if="chatStore.messages.length === 0" class="welcome-section">
          <div class="welcome-icon">
            <el-icon :size="48" color="#409eff"><ChatDotRound /></el-icon>
          </div>
          <h2>您好！我是智能招聘助手</h2>
          <p>我可以帮您了解公司的招聘职位信息，请随时向我提问。</p>
          <div class="suggestions">
            <button
              v-for="suggestion in suggestions"
              :key="suggestion"
              class="suggestion-btn"
              @click="sendSuggestion(suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>

        <div
          v-for="(msg, index) in chatStore.messages"
          :key="index"
          class="message-item"
          :class="msg.role.toLowerCase()"
        >
          <div class="message-avatar">
            <el-avatar v-if="msg.role === 'USER'" :size="36" class="avatar-user">
              <el-icon><User /></el-icon>
            </el-avatar>
            <el-avatar v-else :size="36" class="avatar-ai">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
          </div>
          <div class="message-body">
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
            <div v-if="msg.isStreaming" class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
            <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
              <span class="sources-label">来源职位：</span>
              <el-tag
                v-for="source in msg.sources"
                :key="source.id"
                size="small"
                effect="plain"
                round
              >
                {{ source.title }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 状态提示 -->
      <div v-if="chatStore.currentLayerInfo" class="layer-info">
        <el-icon class="is-loading"><Loading /></el-icon>
        {{ chatStore.currentLayerInfo }}
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <el-input
            v-model="inputMessage"
            placeholder="输入您的问题..."
            :disabled="chatStore.isStreaming || !chatStore.currentSessionId"
            @keyup.enter="sendMessage"
            :rows="2"
            type="textarea"
            resize="none"
          />
          <el-button
            class="send-btn"
            type="primary"
            :disabled="!inputMessage.trim() || chatStore.isStreaming || !chatStore.currentSessionId"
            @click="sendMessage"
            circle
          >
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { User, ChatDotRound, Promotion, Loading } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { marked } from 'marked'

const chatStore = useChatStore()
const inputMessage = ref('')
const messageListRef = ref<HTMLElement>()

const suggestions = [
  '有哪些技术岗位在招聘？',
  '前端开发的薪资待遇如何？',
  '有适合应届生的职位吗？',
]

onMounted(async () => {
  if (!chatStore.currentSessionId && chatStore.sessions.length === 0) {
    await chatStore.createSession()
  }
})

watch(
  () => chatStore.messages.length,
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

watch(
  () => chatStore.messages[chatStore.messages.length - 1]?.content,
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

function formatMessage(content: string): string {
  if (!content) return ''
  return marked(content) as string
}

async function sendMessage() {
  const message = inputMessage.value.trim()
  if (!message || chatStore.isStreaming) return

  inputMessage.value = ''
  await chatStore.sendMessage(message)
}

function sendSuggestion(suggestion: string) {
  inputMessage.value = suggestion
  sendMessage()
}
</script>

<style scoped>
.home-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

/* --- 欢迎区域 --- */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.message-list::-webkit-scrollbar {
  width: 6px;
}

.message-list::-webkit-scrollbar-track {
  background: transparent;
}

.message-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.welcome-section {
  text-align: center;
  padding: 80px 20px 40px;
}

.welcome-icon {
  margin-bottom: 20px;
}

.welcome-section h2 {
  margin-bottom: 8px;
  font-size: 22px;
  font-weight: 600;
  color: #1d2129;
}

.welcome-section p {
  color: #86909c;
  font-size: 15px;
  margin-bottom: 0;
}

.suggestions {
  margin-top: 36px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.suggestion-btn {
  padding: 10px 20px;
  border-radius: 20px;
  border: 1px solid #e4e7ed;
  background: #ffffff;
  color: #4e5969;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-btn:hover {
  background: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
}

/* --- 消息列表 --- */
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  animation: fadeInUp 0.25s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .message-body {
  align-items: flex-end;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar-user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.avatar-ai {
  background: linear-gradient(135deg, #409eff 0%, #36cfc9 100%);
  color: #fff;
}

.message-body {
  display: flex;
  flex-direction: column;
  max-width: 72%;
  min-width: 0;
}

/* --- 消息气泡 --- */
.message-text {
  padding: 14px 18px;
  border-radius: 16px;
  line-height: 1.7;
  font-size: 14px;
  word-break: break-word;
}

/* AI 消息 - 白底深色字 + 左侧边框 */
.message-item.assistant .message-text {
  background: #f0f5ff;
  color: #1d2129;
  border: 1px solid #e0eaff;
  border-radius: 4px 16px 16px 16px;
}

/* 用户消息 - 蓝底白字 */
.message-item.user .message-text {
  background: linear-gradient(135deg, #409eff 0%, #3a7bd5 100%);
  color: #ffffff;
  border-radius: 16px 4px 16px 16px;
}

.message-text :deep(p) {
  margin: 0 0 8px 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(li) {
  margin-bottom: 4px;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message-item.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-text :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 14px 18px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.message-text :deep(strong) {
  font-weight: 600;
}

.message-text :deep(a) {
  color: #409eff;
  text-decoration: underline;
}

.message-item.user .message-text :deep(a) {
  color: #e0eaff;
}

/* --- typing 动画 --- */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 8px 4px;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  background: #409eff;
  border-radius: 50%;
  animation: bounce 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes bounce {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

/* --- 来源标签 --- */
.message-sources {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.sources-label {
  font-size: 12px;
  color: #86909c;
}

/* --- 状态提示 --- */
.layer-info {
  padding: 10px 24px;
  background: linear-gradient(90deg, #f0f9eb 0%, #e1f3d8 100%);
  color: #529b2e;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  border-top: 1px solid #e1f3d8;
}

/* --- 输入区域 --- */
.input-area {
  padding: 16px 24px 20px;
  border-top: 1px solid #f0f2f5;
  background: #fafbfc;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  border-color: #e4e7ed;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper :deep(.el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.send-btn {
  width: 42px;
  height: 42px;
  flex-shrink: 0;
}
</style>

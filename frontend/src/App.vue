<template>
  <div class="app">
    <LoginView v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <template v-else>
      <div class="sidebar-overlay" :class="{ show: sidebarVisible }" @click="sidebarVisible = false"></div>

      <div class="sidebar" :class="{ show: sidebarVisible }">
        <ConversationSidebar
          ref="sidebarRef"
          @select="handleConversationSelect"
          @new="handleNewConversation"
        />
      </div>

      <div class="main-content">
        <div class="main-header">
          <div class="header-left">
            <button class="menu-btn" @click="sidebarVisible = !sidebarVisible">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M3 18H21V16H3V18ZM3 13H21V11H3V13ZM3 6V8H21V6H3Z" fill="currentColor"/>
              </svg>
            </button>
          </div>
          <div class="header-actions">
            <el-dropdown trigger="click" class="action-dropdown">
              <button class="action-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
                </svg>
              </button>
              <template #dropdown>
                <el-dropdown-menu class="action-dropdown-menu">
                  <el-dropdown-item @click="showUploadDialog">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <path d="M9 16H15V10H19L12 3L5 10H9V16ZM5 18V20H19V18H5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    上传文档
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17 7L15.59 8.41L18.17 11H8V13H18.17L15.59 15.58L17 17L22 12L17 7ZM4 5H12V3H4C2.9 3 2 3.9 2 5V19C2 20.1 2.9 21 4 21H12V19H4V5Z"/>
                    </svg>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <ChatView
          ref="chatViewRef"
          :conversation-id="currentConversationId"
          @send="handleSend"
          @done="handleDone"
        />
      </div>

      <DocumentUpload ref="uploadDialogRef" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ConversationSidebar from './components/ConversationSidebar.vue'
import ChatView from './components/ChatView.vue'
import DocumentUpload from './components/DocumentUpload.vue'
import LoginView from './components/LoginView.vue'
import { getConversation } from './api'
import { ElMessage } from 'element-plus'

const sidebarRef = ref(null)
const chatViewRef = ref(null)
const uploadDialogRef = ref(null)
const currentConversationId = ref(null)
const sidebarVisible = ref(false)
const isLoggedIn = ref(false)

onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    isLoggedIn.value = true
  }
})

function handleLoginSuccess() {
  isLoggedIn.value = true
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  isLoggedIn.value = false
  currentConversationId.value = null
  ElMessage.success('已退出')
}

function handleConversationSelect(id) {
  currentConversationId.value = id
  loadConversation(id)
  sidebarVisible.value = false
}

function handleNewConversation() {
  currentConversationId.value = null
  if (chatViewRef.value) chatViewRef.value.messages = []
  sidebarRef.value?.loadConversations()
  sidebarVisible.value = false
}

async function loadConversation(id) {
  try {
    const res = await getConversation(id)
    if (res.data.code === 0 && chatViewRef.value) {
      chatViewRef.value.messages = res.data.data.messages.map(m => ({
        id: m.id, role: m.role, content: m.content,
        time: new Date(m.created_at).toLocaleTimeString(),
        feedback: m.feedback, sources: m.sources,
        tokens: m.tokens_used ? { prompt_tokens: 0, completion_tokens: 0, total_tokens: m.tokens_used } : null,
      }))
    }
  } catch {
    ElMessage.error('加载失败')
  }
}

function handleSend() {}

function handleDone(data) {
  currentConversationId.value = data.conversation_id
  sidebarRef.value?.loadConversations()
}

function showUploadDialog() {
  uploadDialogRef.value?.open()
}
</script>

<style scoped>
.app {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--surface-dark);
}

.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 99;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s;
}

.sidebar-overlay.show {
  opacity: 1;
  pointer-events: auto;
}

.sidebar {
  width: 280px;
  background: var(--surface-dark);
  border-right: 1px solid var(--border-dark-subtle);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--surface-dark);
}

.main-header {
  height: 52px;
  padding: 0 var(--space-24);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-dark-subtle);
  flex-shrink: 0;
  background: var(--surface-dark);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-16);
}

.header-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  color: var(--text-dark-3);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-dark-1);
}

/* Dropdown */
:deep(.action-dropdown-menu) {
  background: var(--surface-dark) !important;
  border: 1px solid var(--border-dark) !important;
  border-radius: var(--radius-sm) !important;
  padding: var(--space-4) !important;
  min-width: 140px !important;
}

:deep(.action-dropdown-menu .el-dropdown-menu__item) {
  color: var(--text-dark-2) !important;
  padding: var(--space-8) var(--space-12) !important;
  font-size: var(--font-sm) !important;
  display: flex !important;
  align-items: center !important;
  gap: var(--space-8) !important;
  border-radius: var(--radius-sm) !important;
}

:deep(.action-dropdown-menu .el-dropdown-menu__item:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
  color: var(--text-dark-1) !important;
}

:deep(.action-dropdown-menu .el-dropdown-menu__item--divided) {
  border-top-color: var(--border-dark-subtle) !important;
  margin-top: var(--space-4) !important;
  padding-top: var(--space-8) !important;
}

.menu-btn {
  display: none;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  color: var(--text-dark-3);
  cursor: pointer;
  border-radius: var(--radius-sm);
  align-items: center;
  justify-content: center;
}

.menu-btn:hover { background: rgba(255, 255, 255, 0.08); }

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0; top: 0;
    height: 100%;
    width: 280px;
    transform: translateX(-100%);
    z-index: 100;
    transition: transform 0.3s;
  }
  .sidebar.show { transform: translateX(0); }
  .menu-btn { display: flex; }
  .main-header { padding: 0 var(--space-16); }
  .user-name { display: none; }
}
</style>

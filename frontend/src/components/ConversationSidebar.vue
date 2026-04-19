<template>
  <div class="conversation-sidebar">
    <div class="sidebar-brand">
      <span class="brand-name">千广传媒</span>
    </div>

    <div class="sidebar-header">
      <button class="new-chat-btn" @click="handleNewConversation">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>新对话</span>
      </button>
    </div>

    <div class="conversation-list">
      <div v-if="conversations.length === 0" class="empty-state">
        <svg width="40" height="40" viewBox="0 0 48 48" fill="none">
          <rect x="8" y="12" width="32" height="24" rx="4" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>
          <path d="M18 22h12M18 28h8" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" stroke-linecap="round"/>
          <circle cx="24" cy="18" r="2" fill="rgba(255,255,255,0.1)"/>
        </svg>
        <p class="empty-title">还没有对话</p>
        <p class="empty-sub">开始第一次提问吧</p>
      </div>

      <div
        v-for="conv in conversations"
        :key="conv.id"
        :class="['conversation-item', { active: conv.id === activeId }]"
        @click="handleSelect(conv.id)"
      >
        <div class="item-info">
          <template v-if="editingId === conv.id">
            <input
              v-model="editingTitle"
              class="edit-input"
              @keyup.enter="saveTitle(conv.id)"
              @keyup.escape="cancelEdit"
              @blur="saveTitle(conv.id)"
              v-focus
            />
          </template>
          <template v-else>
            <span class="item-title">{{ conv.title || '新对话' }}</span>
          </template>
          <span class="item-time">{{ formatDate(conv.updated_at) }}</span>
        </div>
        <div class="item-actions">
          <button class="action-btn" @click.stop="startEdit(conv)" title="重命名">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 17.25V21H6.75L17.81 9.94L14.06 6.19L3 17.25ZM20.71 7.04C21.1 6.65 21.1 6.02 20.71 5.63L18.37 3.29C17.98 2.9 17.35 2.9 16.96 3.29L15.13 5.12L18.88 8.87L20.71 7.04Z"/>
            </svg>
          </button>
          <button class="action-btn delete" @click.stop="handleDelete(conv.id)" title="删除">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19ZM19 4H15.5L14.5 3H9.5L8.5 4H5V6H19V4Z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConversations, deleteConversation, renameConversation } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const emit = defineEmits(['select', 'new'])

const conversations = ref([])
const activeId = ref(null)
const editingId = ref(null)
const editingTitle = ref('')

const vFocus = {
  mounted: (el) => el.focus(),
}

async function loadConversations() {
  try {
    const res = await getConversations()
    conversations.value = res.data.data || []
  } catch (e) {
    console.error('Failed to load conversations:', e)
  }
}

function handleSelect(id) {
  activeId.value = id
  emit('select', id)
}

function handleNewConversation() {
  activeId.value = null
  emit('new')
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定删除此对话？', '提示', { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' })
    const res = await deleteConversation(id)
    if (res.data.code === 0) {
      ElMessage.success('已删除')
      if (activeId.value === id) handleNewConversation()
      loadConversations()
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function startEdit(conv) {
  editingId.value = conv.id
  editingTitle.value = conv.title || '新对话'
}

async function saveTitle(id) {
  if (!editingTitle.value.trim()) { ElMessage.warning('标题不能为空'); return }
  try {
    const res = await renameConversation(id, editingTitle.value.trim())
    if (res.data.code === 0) { ElMessage.success('已重命名'); loadConversations() }
  } catch {
    ElMessage.error('重命名失败')
  }
  editingId.value = null
}

function cancelEdit() { editingId.value = null }

function formatDate(dateStr) {
  const date = new Date(dateStr)
  const diff = Date.now() - date
  if (diff < 3600000) { const m = Math.floor(diff / 60000); return m < 1 ? '刚刚' : `${m}分钟前` }
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return date.toLocaleDateString()
}

onMounted(loadConversations)
defineExpose({ loadConversations })
</script>

<style scoped>
.conversation-sidebar {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface-dark);
}

.sidebar-brand {
  padding: var(--space-20) var(--space-24) var(--space-12);
  border-bottom: 1px solid var(--border-dark-subtle);
}

.brand-name {
  font-family: var(--font-family-heading);
  font-size: 20px;
  font-weight: var(--weight-semibold);
  letter-spacing: -0.4px;
  line-height: 1;
  background: linear-gradient(135deg, #ffffff 40%, #ef2cc1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-header {
  padding: var(--space-20) var(--space-24);
  border-bottom: 1px solid var(--border-dark-subtle);
}

.new-chat-btn {
  width: 100%;
  height: 36px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.87);
  font-family: var(--font-family-body);
  font-size: var(--font-base);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-8);
  border-radius: var(--radius-sm);
  transition: background 0.15s;
  letter-spacing: -0.14px;
}

.new-chat-btn:hover {
  background: rgba(255, 255, 255, 0.18);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-8) var(--space-12);
}

.empty-state {
  text-align: center;
  padding: var(--space-48) var(--space-16);
  color: rgba(255, 255, 255, 0.24);
}

.empty-state svg {
  margin-bottom: var(--space-16);
}

.empty-title {
  font-family: var(--font-family-caption);
  font-size: var(--font-sm);
  color: rgba(255, 255, 255, 0.38);
  margin: 0;
}

.empty-sub {
  font-family: var(--font-family-caption);
  font-size: var(--font-xs);
  color: rgba(255, 255, 255, 0.24);
  margin: var(--space-4) 0 0;
}

.conversation-item {
  padding: var(--space-10) var(--space-12);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.15s;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-2);
}

.conversation-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.conversation-item.active {
  background: rgba(255, 255, 255, 0.12);
}

.item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.item-title {
  font-family: var(--font-family-body);
  font-size: var(--font-base);
  color: rgba(255, 255, 255, 0.87);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: -0.14px;
}

.edit-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-sm);
  color: #ffffff;
  font-family: var(--font-family-body);
  font-size: var(--font-base);
  padding: var(--space-4) var(--space-8);
  outline: none;
  letter-spacing: -0.14px;
}

.edit-input:focus {
  border-color: var(--accent);
}

.conversation-item.active .item-title {
  color: #ffffff;
}

.item-time {
  font-family: var(--font-family-caption);
  font-size: var(--font-sm);
  color: rgba(255, 255, 255, 0.36);
  letter-spacing: 0.055px;
  font-weight: var(--weight-medium);
}

.item-actions {
  display: flex;
  gap: var(--space-2);
  opacity: 0;
  transition: opacity 0.15s;
}

.conversation-item:hover .item-actions {
  opacity: 1;
}

.action-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.38);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
}

.action-btn:hover { background: rgba(255, 255, 255, 0.1); color: rgba(255, 255, 255, 0.87); }
.action-btn.delete:hover { color: var(--red); }
</style>

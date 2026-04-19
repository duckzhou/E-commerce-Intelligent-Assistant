<template>
  <div class="chat-view">
    <div class="messages" ref="messagesRef">
      <!-- Welcome page -->
      <div v-if="messages.length === 0" class="welcome-page">
        <div class="welcome-content">
          <div class="welcome-header">
            <h1 class="welcome-title">你好，今天有什么可以帮你的？</h1>
            <button class="refresh-btn" @click="refreshQuestions">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 4v6h-6"/>
                <path d="M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
              </svg>
              <span>换一批</span>
            </button>
          </div>

          <div class="questions">
            <div
              v-for="(q, i) in currentQuestions"
              :key="i"
              class="question-item"
              @click="quickAsk(q)"
            >
              <span class="question-text">{{ q }}</span>
              <div class="question-divider"></div>
            </div>
          </div>
        </div>

        <!-- Input area -->
        <div class="input-area">
          <div class="input-line">
            <input
              v-model="inputValue"
              type="text"
              placeholder="输入你的问题..."
              class="chat-text-input"
              @keydown="handleKey"
              :disabled="isLoading"
            />
            <button class="send-btn" @click="sendMessage" :disabled="!inputValue.trim() || isLoading">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M5 12h14M13 5l6 7-6 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          <div class="input-bottom">
            <p class="disclaimer">AI 生成内容仅供参考</p>
          </div>
        </div>
      </div>

      <!-- Messages list -->
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-wrapper">
          <div class="avatar assistant-avatar" v-if="msg.role === 'assistant'">
            <svg viewBox="0 0 32 32" width="32" height="32" fill="none">
              <circle cx="16" cy="16" r="14" fill="url(#avatarGrad)"/>
              <rect x="14" y="9" width="4" height="8" rx="2" fill="white" opacity="0.95"/>
              <ellipse cx="16" cy="9" rx="3" ry="4" fill="white" opacity="0.95"/>
              <path d="M9 11c0-3.9 3.1-7 7-7" stroke="white" stroke-width="1.2" stroke-linecap="round" opacity="0.4"/>
              <path d="M23 11c0-3.9-3.1-7-7-7" stroke="white" stroke-width="1.2" stroke-linecap="round" opacity="0.4"/>
              <circle cx="16" cy="22" r="1.2" fill="white" opacity="0.3"/>
              <path d="M12.5 20.5a3.5 3.5 0 007 0" stroke="white" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.25"/>
              <defs>
                <linearGradient id="avatarGrad" x1="2" y1="2" x2="30" y2="30">
                  <stop offset="0%" stop-color="#ef2cc1"/>
                  <stop offset="100%" stop-color="#fc4c02"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div class="message-content">
            <div class="bubble">
              <div class="text" v-if="msg.role === 'user'">{{ msg.content }}</div>
              <div class="text markdown-content" v-else-if="msg.content" v-html="renderMarkdown(msg.content)"></div>
              <div class="typing" v-else>
                <span></span><span></span><span></span>
              </div>
            </div>
            <div v-if="msg.sources && msg.sources.length > 0" class="sources">
              <details>
                <summary>参考来源 ({{ msg.sources.length }})</summary>
                <div v-for="(s, i) in msg.sources" :key="i" class="source-item">
                  {{ s.content }} <span class="source-pct">{{ (s.similarity * 100).toFixed(1) }}%</span>
                </div>
              </details>
            </div>
            <div v-if="msg.tokens" class="token-stats">
              <span class="token-item">输入 <span class="data-num">{{ msg.tokens.prompt_tokens }}</span></span>
              <span class="token-divider"></span>
              <span class="token-item">输出 <span class="data-num">{{ msg.tokens.completion_tokens }}</span></span>
              <span class="token-divider"></span>
              <span class="token-item">总计 <span class="data-num">{{ msg.tokens.total_tokens }}</span></span>
            </div>
            <div class="message-footer">
              <div class="time">{{ msg.time }}</div>
              <div v-if="msg.role === 'assistant' && !msg.loading" class="feedback">
                <button :class="['fb-btn', { active: msg.feedback === 'like' }]" @click="handleFeedback(msg, 'like')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14z"/>
                    <path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"/>
                  </svg>
                </button>
                <button :class="['fb-btn', { active: msg.feedback === 'dislike' }]" @click="handleFeedback(msg, 'dislike')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10z"/>
                    <path d="M17 2h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17"/>
                  </svg>
                </button>
                <button class="fb-btn" @click="copyMessage(msg)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div class="avatar user-avatar" v-if="msg.role === 'user'">
            <span>{{ currentUserInitial }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom input bar (when messages exist) -->
    <div class="input-bar" v-if="messages.length > 0">
      <div class="input-line">
        <input
          v-model="inputValue"
          type="text"
          placeholder="输入你的问题..."
          class="chat-text-input"
          @keydown="handleKey"
          :disabled="isLoading"
        />
        <button class="send-btn" @click="sendMessage" :disabled="!inputValue.trim() || isLoading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M5 12h14M13 5l6 7-6 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { streamChat, updateMessageFeedback } from '../api'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: false, linkify: true, typographer: true, breaks: true })

const props = defineProps({ conversationId: String })
const emit = defineEmits(['send', 'done'])

const messages = ref([])
const inputValue = ref('')
const isLoading = ref(false)
const messagesRef = ref(null)

const currentUserInitial = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user).username?.charAt(0)?.toUpperCase() || 'U' : 'U'
})

const allQuestions = [
  '请介绍一下直播相关的知识库内容',
  '新手主播如何快速积累粉丝？',
  '直播间流量获取有哪些有效方法？',
  '如何规避直播间的违规行为？',
  '直播选品有什么策略和技巧？',
  '如何分析直播数据并优化？',
  '直播设备配置有什么建议？',
  '直播间互动技巧有哪些？',
  '请帮我深度分析一下如何提高直播间转化率',
  '请帮我搜索最新的直播带货趋势和技巧',
]

const questionsPerPage = 4
const currentPage = ref(0)

const currentQuestions = computed(() => {
  const start = currentPage.value * questionsPerPage
  return allQuestions.slice(start, start + questionsPerPage)
})

function quickAsk(q) {
  inputValue.value = q
  sendMessage()
}

function refreshQuestions() {
  currentPage.value = (currentPage.value + 1) % Math.ceil(allQuestions.length / questionsPerPage)
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function renderMarkdown(content) {
  return content ? md.render(content) : ''
}

async function handleFeedback(msg, type) {
  if (!msg.id) { ElMessage.warning('消息ID不存在'); return }
  const newFeedback = msg.feedback === type ? null : type
  try {
    const res = await updateMessageFeedback(msg.id, newFeedback)
    if (res.data.code === 0) {
      msg.feedback = newFeedback
      ElMessage.success(newFeedback ? '感谢反馈' : '已取消')
    }
  } catch {
    ElMessage.error('反馈提交失败')
  }
}

function copyMessage(msg) {
  navigator.clipboard.writeText(msg.content.replace(/[#*`_\[\]()]/g, ''))
    .then(() => ElMessage.success('已复制'))
    .catch(() => ElMessage.error('复制失败'))
}

async function sendMessage() {
  const query = inputValue.value.trim()
  if (!query || isLoading.value) return

  inputValue.value = ''
  isLoading.value = true

  messages.value.push({ role: 'user', content: query, time: new Date().toLocaleTimeString(), id: null })

  const idx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', time: new Date().toLocaleTimeString(), sources: [], feedback: null, id: null, loading: true })

  await nextTick()
  scrollToBottom()
  emit('send', query)

  let scrollCounter = 0
  await streamChat(
    query, props.conversationId,
    (content) => {
      messages.value[idx].content += content
      // 减少滚动频率，每5个chunk滚动一次
      scrollCounter++
      if (scrollCounter % 5 === 0) {
        scrollToBottom()
      }
    },
    (data) => {
      isLoading.value = false
      messages.value[idx].loading = false
      if (data.sources) messages.value[idx].sources = data.sources
      if (data.tokens) messages.value[idx].tokens = data.tokens
      if (data.message_id) messages.value[idx].id = data.message_id
      emit('done', data)
      scrollToBottom()
    },
    (error) => {
      isLoading.value = false
      messages.value[idx].loading = false
      messages.value[idx].content = `错误: ${error}`
      ElMessage.error('发送失败: ' + error)
    }
  )
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })
}

defineExpose({ messages })
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--surface-dark);
  position: relative;
}

.messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* Welcome page */
.welcome-page {
  display: flex;
  flex-direction: column;
  padding: var(--space-48) var(--space-48) var(--space-64);
  max-width: 700px;
  margin: 0 auto;
  width: 100%;
}

.welcome-content {
  max-width: 700px;
  width: 100%;
  margin: 0 auto;
}

.welcome-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: var(--space-32);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  background: transparent;
  border: none;
  color: var(--text-dark-3);
  font-family: var(--font-family-caption);
  font-size: var(--font-sm);
  cursor: pointer;
  padding: var(--space-6) var(--space-8);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
  white-space: nowrap;
  flex-shrink: 0;
}

.refresh-btn:hover {
  color: var(--text-dark-1);
  background: rgba(255, 255, 255, 0.08);
}

.welcome-title {
  font-family: var(--font-family-heading);
  font-size: 40px;
  font-weight: var(--weight-medium);
  color: var(--text-dark-1);
  letter-spacing: -0.8px;
  line-height: 1.2;
  margin: 0;
}

.questions {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.question-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-12) 0;
  cursor: pointer;
  transition: opacity 0.15s;
  position: relative;
}

.question-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-dark-subtle);
}

.question-item:hover {
  opacity: 0.8;
}

.question-text {
  font-family: var(--font-family-body);
  font-size: var(--font-md);
  color: var(--text-dark-2);
  letter-spacing: -0.15px;
}

.question-item:hover .question-text {
  color: var(--text-dark-1);
}

.question-divider {
  display: none;
}

/* Input area */
.input-area {
  margin-top: var(--space-32);
}

.input-line {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-dark);
  border-radius: var(--radius-sm);
  padding: 0 var(--space-16);
  height: 48px;
  gap: var(--space-12);
}

.chat-text-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-family: var(--font-family-body);
  font-size: var(--font-md);
  color: var(--text-dark-1);
  letter-spacing: -0.16px;
}

.chat-text-input::placeholder {
  color: var(--text-dark-3);
}

.send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ef2cc1, #fc4c02);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.send-btn:disabled {
  opacity: 0.25;
  cursor: not-allowed;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.2);
}

.disclaimer {
  font-family: var(--font-family-caption);
  font-size: var(--font-sm);
  color: var(--text-dark-3);
  margin: var(--space-12) 0 0;
  letter-spacing: 0.055px;
  font-weight: var(--weight-medium);
}

.input-bottom {
  margin-top: var(--space-12);
}

/* Messages */
.message {
  padding: var(--space-20) var(--space-24);
  border-bottom: 1px solid var(--border-dark-subtle);
}

.message.user {
  background: rgba(255, 255, 255, 0.03);
}

.message-wrapper {
  display: flex;
  gap: var(--space-16);
  max-width: 640px;
  margin: 0 auto;
  align-items: flex-start;
}

.message.user .message-wrapper {
  flex-direction: row-reverse;
}

.avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: var(--font-sm);
  font-weight: var(--weight-bold);
}

.assistant-avatar {
  border-radius: var(--radius-sm);
}

.user-avatar {
  background: linear-gradient(135deg, #ef2cc1, #fc4c02);
  color: #ffffff;
  border-radius: var(--radius-sm);
  font-weight: var(--weight-medium);
}

.message-content {
  max-width: calc(100% - 50px);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.message.user .message-content {
  align-items: flex-end;
}

.bubble {
  padding: var(--space-4) 0;
  font-family: var(--font-family-body);
  font-size: var(--font-md);
  line-height: 1.7;
  word-break: break-word;
}

.message.user .bubble {
  color: var(--text-dark-1);
}

.message.assistant .bubble {
  color: var(--text-dark-2);
}

.token-stats {
  display: flex;
  gap: var(--space-8);
  align-items: center;
  padding: var(--space-6) var(--space-12);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-dark-subtle);
  border-radius: var(--radius-sm);
  font-family: var(--font-family-data);
  font-size: var(--font-xs);
  color: var(--text-dark-3);
}

.data-num {
  color: var(--accent);
  font-weight: var(--weight-medium);
}

.token-divider {
  width: 1px;
  height: 12px;
  background: var(--border-dark-subtle);
}

.message-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.time {
  font-family: var(--font-family-caption);
  font-size: var(--font-xs);
  color: var(--text-dark-4);
}

.feedback {
  display: flex;
  gap: var(--space-2);
}

.fb-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  background: transparent;
  color: var(--text-dark-4);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  border-radius: var(--radius-sm);
}

.fb-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-dark-2);
}

.fb-btn.active {
  color: var(--green);
}

.sources {
  padding: var(--space-8) var(--space-12);
  background: rgba(239, 44, 193, 0.06);
  border: 1px solid rgba(239, 44, 193, 0.15);
  border-radius: var(--radius-sm);
  font-size: var(--font-sm);
  color: var(--text-dark-2);
}

.sources summary {
  cursor: pointer;
  color: var(--text-dark-2);
  font-weight: var(--weight-medium);
  font-family: var(--font-family-caption);
  font-size: var(--font-xs);
  letter-spacing: 0.055px;
}

.source-item {
  padding: var(--space-6) var(--space-8);
  margin-top: var(--space-6);
  background: rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--accent);
  color: var(--text-dark-3);
  font-size: var(--font-xs);
  font-family: var(--font-family-body);
}

.source-pct {
  font-family: var(--font-family-data);
  color: var(--accent);
  margin-left: var(--space-4);
}

/* Bottom input bar */
.input-bar {
  padding: var(--space-12) var(--space-24);
  border-top: 1px solid var(--border-dark-subtle);
  background: var(--surface-dark);
}

.input-bar .input-line {
  max-width: 700px;
  margin: 0 auto;
}

.typing {
  display: flex;
  gap: var(--space-6);
  padding: var(--space-8) 0;
}

.typing span {
  width: 6px;
  height: 6px;
  background: var(--text-dark-3);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

@media (max-width: 768px) {
  .chat-view { height: 100dvh; }
  .welcome-page {
    padding: var(--space-32) var(--space-20) var(--space-24);
  }
  .welcome-header { flex-direction: column; align-items: flex-start; gap: var(--space-12); margin-bottom: var(--space-24); }
  .welcome-title { font-size: 28px; letter-spacing: -0.56px; }
  .message { padding: var(--space-16) var(--space-16); }
  .message-wrapper { max-width: 100%; }
}
</style>

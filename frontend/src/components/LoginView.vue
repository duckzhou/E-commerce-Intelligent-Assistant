<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Brand -->
      <div class="brand-zone">
        <h1 class="brand-name">千广传媒</h1>
        <p class="brand-sub">主播智能助手</p>
      </div>

      <!-- Login / Register card -->
      <div class="form-card">
        <div v-if="isLogin" class="form-area">
          <div class="input-group">
            <label class="input-label">用户名</label>
            <input
              v-model="loginForm.username"
              type="text"
              placeholder="输入用户名"
              class="text-input"
              @keyup.enter="handleLogin"
            />
          </div>
          <div class="input-group">
            <label class="input-label">密码</label>
            <input
              v-model="loginForm.password"
              type="password"
              placeholder="输入密码"
              class="text-input"
              @keyup.enter="handleLogin"
            />
          </div>
          <button class="submit-btn" @click="handleLogin" :disabled="loading">
            {{ loading ? '登录中...' : '登 录' }}
          </button>
          <p class="form-footer">
            没有账号？<a class="link" @click="isLogin = false">注册</a>
          </p>
        </div>

        <div v-else class="form-area">
          <div class="input-group">
            <label class="input-label">用户名</label>
            <input v-model="registerForm.username" type="text" placeholder="输入用户名" class="text-input" />
          </div>
          <div class="input-group">
            <label class="input-label">邮箱</label>
            <input v-model="registerForm.email" type="email" placeholder="输入邮箱" class="text-input" />
          </div>
          <div class="input-group">
            <label class="input-label">姓名</label>
            <input v-model="registerForm.fullName" type="text" placeholder="输入姓名（可选）" class="text-input" />
          </div>
          <div class="input-group">
            <label class="input-label">密码</label>
            <input v-model="registerForm.password" type="password" placeholder="设置密码" class="text-input" />
          </div>
          <div class="input-group">
            <label class="input-label">确认密码</label>
            <input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="再次输入密码"
              class="text-input"
              @keyup.enter="handleRegister"
            />
          </div>
          <button class="submit-btn" @click="handleRegister" :disabled="loading">
            {{ loading ? '注册中...' : '注 册' }}
          </button>
          <p class="form-footer">
            已有账号？<a class="link" @click="isLogin = true">登录</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const isLogin = ref(true)
const loading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', fullName: '', password: '', confirmPassword: '' })

const emit = defineEmits(['login-success'])

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  loading.value = true
  try {
    const res = await axios.post(`${API_BASE}/auth/login`, loginForm)
    if (res.data.access_token) {
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      ElMessage.success('登录成功')
      emit('login-success', res.data.user)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查网络')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.email || !registerForm.password) {
    ElMessage.warning('请填写必填项')
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.error('两次密码不一致')
    return
  }
  loading.value = true
  try {
    const res = await axios.post(`${API_BASE}/auth/register`, {
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      full_name: registerForm.fullName || null,
    })
    if (res.data.access_token) {
      ElMessage.success('注册成功，请登录')
      isLogin.value = true
      loginForm.username = registerForm.username
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(145deg, #e8d5f5 0%, #d5e0f5 35%, #f5e0e8 70%, #f0d5f0 100%);
  position: relative;
  overflow-x: hidden;
}

/* Container */
.login-container {
  padding: 0 var(--space-24);
  max-width: 440px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: var(--space-64);
}

/* Brand zone */
.brand-zone {
  text-align: center;
  margin-bottom: var(--space-8);
}

.brand-name {
  font-family: var(--font-family-heading);
  font-size: var(--font-3xl);
  font-weight: var(--weight-semibold);
  letter-spacing: -0.4px;
  line-height: 1;
  margin: 0;
  background: linear-gradient(135deg, #1a1a2e 40%, #ef2cc1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-sub {
  font-family: var(--font-family-body);
  font-size: var(--font-lg);
  color: var(--text-2);
  margin: var(--space-4) 0 0;
  font-weight: var(--weight-medium);
  letter-spacing: -0.18px;
}

/* Form card */
.form-card {
  width: 100%;
  background: #ffffff;
  border-radius: var(--radius-md);
  padding: var(--space-32);
  border: 1px solid var(--border-1);
  box-shadow: var(--shadow-md);
}

.form-area {
  width: 100%;
}

.input-group {
  margin-bottom: var(--space-16);
}

.input-label {
  display: block;
  font-family: var(--font-family-body);
  font-size: var(--font-base);
  font-weight: var(--weight-medium);
  color: var(--text-1);
  margin-bottom: var(--space-6);
  letter-spacing: -0.14px;
}

.text-input {
  width: 100%;
  height: 48px;
  background: #ffffff;
  border: 1px solid var(--border-1);
  border-radius: var(--radius-sm);
  outline: none;
  font-family: var(--font-family-body);
  font-size: var(--font-md);
  color: var(--text-1);
  padding: 0 var(--space-12);
  transition: border-color 0.15s;
  letter-spacing: -0.16px;
}

.text-input:focus {
  border-color: var(--accent);
}

.text-input::placeholder {
  color: var(--text-4);
}

.submit-btn {
  margin-top: var(--space-24);
  width: 100%;
  height: 48px;
  background: var(--navy);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-family-body);
  font-size: var(--font-md);
  font-weight: var(--weight-medium);
  cursor: pointer;
  transition: opacity 0.15s;
  letter-spacing: -0.16px;
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.form-footer {
  margin-top: var(--space-20);
  font-family: var(--font-family-body);
  font-size: var(--font-sm);
  color: var(--text-3);
  text-align: center;
  letter-spacing: -0.14px;
}

.link {
  color: var(--accent);
  cursor: pointer;
  text-decoration: none;
  margin-left: var(--space-4);
  font-weight: var(--weight-medium);
}

.link:hover {
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 768px) {
  .login-page {
    justify-content: center;
    padding-top: 0;
  }
  .login-container {
    padding: 0 var(--space-16);
  }
  .brand-name { font-size: var(--font-2xl); }
  .brand-sub { font-size: var(--font-md); }
  .form-card { padding: var(--space-24); }
  .form-title { font-size: var(--font-lg); }
}
</style>

<template>
  <el-dialog
    v-model="visible"
    width="440px"
    :show-close="true"
    class="upload-dialog"
  >
    <template #header>
      <h3 class="dialog-title">上传文档</h3>
    </template>

    <div class="upload-body">
      <div
        class="upload-zone"
        @click="triggerFileInput"
        @drop.prevent="handleDrop"
        @dragover.prevent
        :class="{ 'drag-over': isDragOver }"
      >
        <input ref="fileInput" type="file" accept=".txt,.pdf" @change="handleFileSelect" class="file-input" />

        <div v-if="!selectedFile" class="upload-placeholder">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <path d="M9 16H15V10H19L12 3L5 10H9V16ZM5 18V20H19V18H5Z" stroke="rgba(255,255,255,0.38)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p class="upload-text">拖拽文件到此处，或点击上传</p>
          <p class="upload-info">支持 .txt 和 .pdf</p>
        </div>

        <div v-else class="file-info">
          <span class="file-name">{{ selectedFile.name }}</span>
          <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
          <button class="remove-btn" @click.stop="removeFile">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <button class="btn-cancel" @click="visible = false">取消</button>
        <button class="btn-upload" @click="handleUpload" :disabled="!selectedFile || uploading">
          {{ uploading ? '上传中...' : '上传' }}
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { uploadDocument } from '../api'
import { ElMessage } from 'element-plus'

const visible = ref(false)
const selectedFile = ref(null)
const uploading = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)

function open() { visible.value = true; selectedFile.value = null }
function triggerFileInput() { fileInput.value?.click() }

function handleFileSelect(e) {
  if (e.target.files[0]) validateAndSetFile(e.target.files[0])
}

function handleDrop(e) {
  if (e.dataTransfer.files.length > 0) validateAndSetFile(e.dataTransfer.files[0])
}

function validateAndSetFile(file) {
  const valid = ['text/plain', 'application/pdf', '.txt', '.pdf']
  const ok = valid.includes(file.type) || valid.some(ext => file.name.toLowerCase().endsWith(ext))
  if (!ok) { ElMessage.error('仅支持 .txt 和 .pdf'); return }
  if (file.size > 10 * 1024 * 1024) { ElMessage.error('文件不超过 10MB'); return }
  selectedFile.value = file
}

function removeFile() {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

async function handleUpload() {
  if (!selectedFile.value) { ElMessage.warning('请先选择文件'); return }
  uploading.value = true
  try {
    const res = await uploadDocument(selectedFile.value)
    if (res.code === 0) { ElMessage.success('上传成功'); visible.value = false }
    else ElMessage.error('上传失败: ' + res.message)
  } catch (e) {
    ElMessage.error('上传失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}

defineExpose({ open })
</script>

<style scoped>
.upload-zone {
  border: 1px dashed var(--border-dark);
  border-radius: var(--radius-sm);
  padding: var(--space-32) var(--space-24);
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: rgba(255, 255, 255, 0.38);
  background: rgba(255, 255, 255, 0.04);
}

.file-input { display: none }

.upload-placeholder .upload-text {
  font-size: var(--font-md);
  color: var(--text-dark-2);
  margin: var(--space-12) 0 var(--space-4);
}

.upload-placeholder .upload-info {
  font-size: var(--font-sm);
  color: var(--text-dark-4);
  margin: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: var(--space-12);
}

.file-name {
  flex: 1;
  font-family: var(--font-family-caption);
  font-size: var(--font-sm);
  color: var(--text-dark-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}

.file-size {
  font-family: var(--font-family-data);
  font-size: var(--font-xs);
  color: var(--text-dark-4);
}

.remove-btn {
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  color: var(--text-dark-4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
}

.remove-btn:hover { color: var(--text-dark-2); background: rgba(255,255,255,0.08); }

.dialog-title {
  font-family: var(--font-family-heading);
  font-size: var(--font-lg);
  font-weight: var(--weight-medium);
  color: var(--text-dark-1);
  margin: 0;
  letter-spacing: -0.18px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-12);
}

.btn-cancel {
  padding: var(--space-8) var(--space-20);
  background: transparent;
  border: 1px solid var(--border-dark);
  color: var(--text-dark-2);
  cursor: pointer;
  font-family: var(--font-family-caption);
  font-size: var(--font-sm);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.btn-cancel:hover { border-color: var(--border-dark); background: rgba(255,255,255,0.06); }

.btn-upload {
  padding: var(--space-8) var(--space-20);
  background: linear-gradient(135deg, #ef2cc1, #fc4c02);
  border: none;
  color: #ffffff;
  cursor: pointer;
  font-family: var(--font-family-caption);
  font-size: var(--font-sm);
  font-weight: var(--weight-medium);
  border-radius: var(--radius-sm);
  transition: opacity 0.15s;
}

.btn-upload:hover:not(:disabled) { opacity: 0.85; }
.btn-upload:disabled { opacity: 0.4; cursor: not-allowed; }
</style>

<style>
/* Unscoped — Element Plus dialog is teleported to body */
.upload-dialog.el-dialog {
  background: #010120 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}

.upload-dialog .el-dialog__header {
  padding: 20px 24px 16px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
  margin: 0 !important;
}

.upload-dialog .el-dialog__title {
  color: #ffffff !important;
}

.upload-dialog .el-dialog__body {
  padding: 24px !important;
  color: rgba(255, 255, 255, 0.87) !important;
}

.upload-dialog .el-dialog__footer {
  padding: 16px 24px !important;
  border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
}

.upload-dialog .el-dialog__close {
  color: rgba(255, 255, 255, 0.38) !important;
}

.upload-dialog .el-dialog__close:hover {
  color: rgba(255, 255, 255, 0.87) !important;
}
</style>

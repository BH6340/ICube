<script setup>
/**
 * AppDownloadDialog.vue — APP 下载弹窗
 *
 * 显示二维码供手机扫描下载，同时提供直接下载链接。
 * 版本信息从后端 /api/home/app/version/ 获取。
 */
import { ref, watch, nextTick } from 'vue'
import QRCode from 'qrcode'
import { getAppVersionApi } from '@/api/home'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(props.modelValue)
const version = ref('')
const downloadUrl = ref('')
const updateInfo = ref('')
const loading = ref(false)
const canvasRef = ref(null)

watch(() => props.modelValue, async (val) => {
  visible.value = val
  if (val) {
    await fetchVersion()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

async function fetchVersion() {
  loading.value = true
  try {
    const res = await getAppVersionApi()
    const data = res.data || res
    version.value = data.version || '1.0.0'
    downloadUrl.value = data.download_url || '/apk/icube-v1.0.0.apk'
    updateInfo.value = data.update_info || ''
    await nextTick()
    if (canvasRef.value) {
      await QRCode.toCanvas(canvasRef.value, downloadUrl.value, {
        width: 200,
        margin: 2,
        color: { dark: '#1a1a2e', light: '#ffffff' },
      })
    }
  } catch {
    downloadUrl.value = '/apk/icube-v1.0.0.apk'
    await nextTick()
    if (canvasRef.value) {
      await QRCode.toCanvas(canvasRef.value, downloadUrl.value, {
        width: 200,
        margin: 2,
        color: { dark: '#1a1a2e', light: '#ffffff' },
      })
    }
  } finally {
    loading.value = false
  }
}

function directDownload() {
  if (downloadUrl.value) {
    window.open(downloadUrl.value, '_blank')
  }
}
</script>

<template>
  <el-dialog
    v-model="visible"
    title="下载 ICube APP"
    width="360px"
    :show-close="true"
    align-center
    class="app-download-dialog"
  >
    <div class="download-body">
      <div class="qr-section">
        <canvas ref="canvasRef" class="qr-canvas"></canvas>
        <p class="qr-tip">手机扫码下载安装</p>
      </div>
      <el-divider direction="vertical" class="divider" />
      <div class="direct-section">
        <el-icon :size="32" color="#409eff"><Download /></el-icon>
        <p class="direct-tip">电脑端直接下载</p>
        <el-button type="primary" :loading="loading" @click="directDownload">
          下载 APK
        </el-button>
        <p v-if="version" class="version-text">当前版本 v{{ version }}</p>
        <p v-if="updateInfo" class="update-info">{{ updateInfo }}</p>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.download-body {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0 4px;
  gap: 8px;
}

.qr-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.qr-canvas {
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.qr-tip {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.divider {
  height: 200px;
}

.direct-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  min-width: 120px;
}

.direct-tip {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.version-text {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin: 0;
}

.update-info {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin: 0;
  text-align: center;
}

@media (max-width: 480px) {
  .download-body {
    flex-direction: column;
    gap: 16px;
  }

  .divider {
    height: 1px;
    width: 80%;
  }
}
</style>

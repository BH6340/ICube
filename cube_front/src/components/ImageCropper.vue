<template>
  <div class="image-cropper-overlay" @click="handleClose" @wheel.prevent="onWheel">
    <div class="image-cropper" @click.stop @wheel.prevent="onWheel">
      <div class="cropper-header">
        <h3>{{ title }}</h3>
        <button class="close-btn" @click="handleClose">×</button>
      </div>

      <div class="cropper-body">
        <div class="crop-area" ref="cropAreaRef" @wheel.prevent="onWheel">
          <canvas 
            ref="canvasRef" 
            @mousedown="startDrag"
          />
          <div class="crop-mask"></div>
          <div class="crop-frame"></div>
        </div>

        <div class="controls">
          <div class="zoom-controls">
            <button type="button" @click="zoomOut">-</button>
            <span>{{ Math.round(scale * 100) }}%</span>
            <button type="button" @click="zoomIn">+</button>
          </div>
          <div class="action-controls">
            <button type="button" class="btn-cancel" @click="handleClose">取消</button>
            <button type="button" class="btn-confirm" @click="confirmCrop">确认裁剪</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  imageFile: {
    type: File,
    required: true
  },
  title: {
    type: String,
    default: '图片裁剪'
  }
})

const emit = defineEmits(['close', 'crop'])

const canvasRef = ref(null)
const cropAreaRef = ref(null)
const scale = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const startY = ref(0)
const originalImage = ref(null)

const FRAME_SIZE = 350
const FRAME_OFFSET = 55
const CANVAS_SIZE = 460

function preprocessImage(file) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        const maxSize = 2048
        let { width, height } = img
        
        if (width > maxSize || height > maxSize) {
          const ratio = Math.min(maxSize / width, maxSize / height)
          width = Math.round(width * ratio)
          height = Math.round(height * ratio)
          
          const canvas = document.createElement('canvas')
          canvas.width = width
          canvas.height = height
          const ctx = canvas.getContext('2d')
          ctx.imageSmoothingEnabled = true
          ctx.imageSmoothingQuality = 'high'
          ctx.drawImage(img, 0, 0, width, height)
          resolve(canvas)
        } else {
          resolve(img)
        }
      }
      img.src = e.target.result
    }
    reader.readAsDataURL(file)
  })
}

onMounted(async () => {
  originalImage.value = await preprocessImage(props.imageFile)
  
  await nextTick()
  
  initCanvas()
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', endDrag)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', endDrag)
})

function initCanvas() {
  if (!canvasRef.value || !originalImage.value) return
  
  const canvas = canvasRef.value
  canvas.width = CANVAS_SIZE
  canvas.height = CANVAS_SIZE
  
  const img = originalImage.value
  
  if (img.naturalWidth <= CANVAS_SIZE && img.naturalHeight <= CANVAS_SIZE) {
    scale.value = 1
  } else {
    const ratio = Math.min(CANVAS_SIZE / img.naturalWidth, CANVAS_SIZE / img.naturalHeight)
    scale.value = ratio
  }
  
  offsetX.value = (CANVAS_SIZE - img.naturalWidth * scale.value) / 2
  offsetY.value = (CANVAS_SIZE - img.naturalHeight * scale.value) / 2
  
  drawCanvas()
}

function drawCanvas() {
  if (!canvasRef.value || !originalImage.value) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  
  ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
  
  ctx.save()
  ctx.drawImage(
    originalImage.value,
    offsetX.value,
    offsetY.value,
    originalImage.value.naturalWidth * scale.value,
    originalImage.value.naturalHeight * scale.value
  )
  ctx.restore()
}

function startDrag(e) {
  isDragging.value = true
  startX.value = e.clientX
  startY.value = e.clientY
}

function onDrag(e) {
  if (!isDragging.value) return
  
  const deltaX = e.clientX - startX.value
  const deltaY = e.clientY - startY.value
  
  offsetX.value += deltaX
  offsetY.value += deltaY
  
  startX.value = e.clientX
  startY.value = e.clientY
  
  drawCanvas()
}

function endDrag() {
  isDragging.value = false
}

function zoomIn() {
  scale.value = Math.min(5, scale.value + 0.1)
  drawCanvas()
}

function zoomOut() {
  scale.value = Math.max(0.2, scale.value - 0.1)
  drawCanvas()
}

function onWheel(e) {
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  scale.value = Math.max(0.2, Math.min(5, scale.value + delta))
  drawCanvas()
}

function confirmCrop() {
  if (!originalImage.value) return
  
  const img = originalImage.value
  
  const sourceX = (FRAME_OFFSET - offsetX.value) / scale.value
  const sourceY = (FRAME_OFFSET - offsetY.value) / scale.value
  const sourceSize = FRAME_SIZE / scale.value
  
  const canvas = document.createElement('canvas')
  canvas.width = 512
  canvas.height = 512
  
  const ctx = canvas.getContext('2d')
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  
  ctx.drawImage(
    img,
    sourceX,
    sourceY,
    sourceSize,
    sourceSize,
    0,
    0,
    512,
    512
  )
  
  canvas.toBlob((blob) => {
    if (!blob) {
      emit('close')
      return
    }
    const croppedFile = new File([blob], props.imageFile.name.replace(/\.[^/.]+$/, '') + '_cropped.webp', {
      type: 'image/webp'
    })
    emit('crop', croppedFile)
  }, 'image/webp', 0.85)
}

function handleClose() {
  emit('close')
}
</script>

<style scoped>
.image-cropper-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.image-cropper {
  width: 500px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.cropper-header {
  height: 50px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #eee;
}

.cropper-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.close-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
}

.cropper-body {
  padding: 20px;
}

.crop-area {
  width: 460px;
  height: 460px;
  border: 1px solid #ddd;
  overflow: hidden;
  position: relative;
  background: #f5f5f5;
}

canvas {
  cursor: move;
  display: block;
}

.crop-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  border: 55px solid rgba(0, 0, 0, 0);
  box-sizing: border-box;
  pointer-events: none;
}

.crop-frame {
  position: absolute;
  top: 55px;
  left: 55px;
  width: 350px;
  height: 350px;
  border: 2px dashed #1890ff;
  pointer-events: none;
}

.controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.zoom-controls button {
  width: 36px;
  height: 36px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.zoom-controls button:hover {
  background: #f5f5f5;
}

.zoom-controls span {
  font-size: 14px;
  color: #666;
  min-width: 60px;
  text-align: center;
}

.action-controls {
  display: flex;
  gap: 15px;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 24px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  border: none;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-confirm {
  background: #1890ff;
  color: #fff;
}

.btn-confirm:hover {
  background: #40a9ff;
}
</style>
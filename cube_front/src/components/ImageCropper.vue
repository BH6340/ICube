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
/**
 * 图片裁剪组件
 *
 * 提供 1:1 固定比例的图片裁剪功能，支持拖拽和缩放操作。
 *
 * 功能特性：
 *   - Canvas 实现的高质量裁剪
 *   - 支持鼠标拖拽移动图片
 *   - 支持滚轮缩放和按钮缩放
 *   - 裁剪输出 512x512 WebP 格式图片
 *   - 大图自动预压缩（>2048px 时）
 *
 * Props:
 *   - imageFile: 要裁剪的图片文件（必填）
 *   - title: 裁剪对话框标题（默认 "图片裁剪"）
 *
 * Emits:
 *   - close: 关闭裁剪对话框
 *   - crop: 裁剪完成，传递裁剪后的文件
 */

import { ref, onMounted, onUnmounted, nextTick } from 'vue'

// 组件属性定义
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

// 组件事件定义
const emit = defineEmits(['close', 'crop'])

// 模板引用
const canvasRef = ref(null)      // Canvas 元素引用
const cropAreaRef = ref(null)    // 裁剪区域引用

// 状态变量
const scale = ref(1)             // 缩放比例
const offsetX = ref(0)           // 图片水平偏移
const offsetY = ref(0)           // 图片垂直偏移
const isDragging = ref(false)    // 是否正在拖拽
const startX = ref(0)            // 拖拽起始X坐标
const startY = ref(0)            // 拖拽起始Y坐标
const originalImage = ref(null)  // 原始图片对象（预压缩后）

// 常量定义
const FRAME_SIZE = 350           // 裁剪框尺寸（像素）
const FRAME_OFFSET = 55          // 裁剪框偏移量
const CANVAS_SIZE = 460          // Canvas 画布尺寸

/**
 * 图片预压缩处理
 *
 * 对大图进行预压缩（>2048px），避免在 Canvas 上渲染过大的图片。
 * 使用等比例缩放算法，保持图片宽高比。
 *
 * @param {File} file - 原始图片文件
 * @returns {Promise<HTMLImageElement|HTMLCanvasElement>} - 处理后的图片对象
 */
function preprocessImage(file) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        const maxSize = 2048
        let { width, height } = img
        
        // 如果图片超过最大尺寸，进行预压缩
        if (width > maxSize || height > maxSize) {
          const ratio = Math.min(maxSize / width, maxSize / height)
          width = Math.round(width * ratio)
          height = Math.round(height * ratio)
          
          // 创建临时 Canvas 进行缩放
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

/**
 * 组件挂载生命周期
 *
 * 初始化图片、Canvas 和事件监听。
 */
onMounted(async () => {
  // 预压缩图片
  originalImage.value = await preprocessImage(props.imageFile)
  
  // 等待 DOM 更新
  await nextTick()
  
  // 初始化 Canvas
  initCanvas()
  
  // 添加全局鼠标事件监听，实现流畅拖拽
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', endDrag)
})

/**
 * 组件卸载生命周期
 *
 * 移除全局事件监听，防止内存泄漏。
 */
onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', endDrag)
})

/**
 * 初始化 Canvas
 *
 * 根据图片尺寸自动计算初始缩放比例和位置，
 * 确保图片居中显示在裁剪区域内。
 */
function initCanvas() {
  if (!canvasRef.value || !originalImage.value) return
  
  const canvas = canvasRef.value
  canvas.width = CANVAS_SIZE
  canvas.height = CANVAS_SIZE
  
  const img = originalImage.value
  
  // 计算初始缩放比例：使图片适应 Canvas
  if (img.naturalWidth <= CANVAS_SIZE && img.naturalHeight <= CANVAS_SIZE) {
    scale.value = 1
  } else {
    const ratio = Math.min(CANVAS_SIZE / img.naturalWidth, CANVAS_SIZE / img.naturalHeight)
    scale.value = ratio
  }
  
  // 计算居中偏移
  offsetX.value = (CANVAS_SIZE - img.naturalWidth * scale.value) / 2
  offsetY.value = (CANVAS_SIZE - img.naturalHeight * scale.value) / 2
  
  drawCanvas()
}

/**
 * 绘制 Canvas 内容
 *
 * 根据当前的偏移和缩放参数，将图片绘制到 Canvas 上。
 */
function drawCanvas() {
  if (!canvasRef.value || !originalImage.value) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  
  // 清空画布
  ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
  
  // 保存状态并绘制图片
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

/**
 * 开始拖拽
 *
 * 记录拖拽起始位置，配合 mousemove 事件实现图片拖拽。
 *
 * @param {MouseEvent} e - 鼠标按下事件
 */
function startDrag(e) {
  isDragging.value = true
  startX.value = e.clientX
  startY.value = e.clientY
}

/**
 * 拖拽中处理
 *
 * 根据鼠标移动距离更新图片偏移，实现流畅的拖拽效果。
 * 通过全局 mousemove 事件监听，即使鼠标移出裁剪区域也能持续响应。
 *
 * @param {MouseEvent} e - 鼠标移动事件
 */
function onDrag(e) {
  if (!isDragging.value) return
  
  // 计算偏移量
  const deltaX = e.clientX - startX.value
  const deltaY = e.clientY - startY.value
  
  offsetX.value += deltaX
  offsetY.value += deltaY
  
  // 更新起始位置
  startX.value = e.clientX
  startY.value = e.clientY
  
  drawCanvas()
}

/**
 * 结束拖拽
 *
 * 鼠标释放时停止拖拽状态。
 */
function endDrag() {
  isDragging.value = false
}

/**
 * 放大
 *
 * 每次点击放大 10%，最大 5 倍。
 */
function zoomIn() {
  scale.value = Math.min(5, scale.value + 0.1)
  drawCanvas()
}

/**
 * 缩小
 *
 * 每次点击缩小 10%，最小 0.2 倍。
 */
function zoomOut() {
  scale.value = Math.max(0.2, scale.value - 0.1)
  drawCanvas()
}

/**
 * 滚轮缩放
 *
 * 支持鼠标滚轮缩放，向上放大，向下缩小。
 * 缩放步长为 0.1，范围 0.2-5 倍。
 *
 * @param {WheelEvent} e - 滚轮事件
 */
function onWheel(e) {
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  scale.value = Math.max(0.2, Math.min(5, scale.value + delta))
  drawCanvas()
}

/**
 * 确认裁剪
 *
 * 根据当前裁剪框位置和大小，从原图中提取对应区域，
 * 输出 512x512 的 WebP 格式裁剪图片。
 *
 * 计算逻辑：
 *   - sourceX/Y: 裁剪框在原图中的起始位置
 *   - sourceSize: 裁剪框在原图中的尺寸
 *   - 输出尺寸: 固定为 512x512
 *
 * 触发事件：
 *   - emit('crop', croppedFile): 传递裁剪后的文件
 */
function confirmCrop() {
  if (!originalImage.value) return
  
  const img = originalImage.value
  
  // 计算原图中裁剪区域的位置和大小
  const sourceX = (FRAME_OFFSET - offsetX.value) / scale.value
  const sourceY = (FRAME_OFFSET - offsetY.value) / scale.value
  const sourceSize = FRAME_SIZE / scale.value
  
  // 创建输出 Canvas
  const canvas = document.createElement('canvas')
  canvas.width = 512
  canvas.height = 512
  
  const ctx = canvas.getContext('2d')
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  
  // 从原图裁剪区域绘制到输出 Canvas
  ctx.drawImage(
    img,
    sourceX,           // 源X坐标
    sourceY,           // 源Y坐标
    sourceSize,        // 源宽度
    sourceSize,        // 源高度
    0,                 // 目标X坐标
    0,                 // 目标Y坐标
    512,               // 目标宽度
    512                // 目标高度
  )
  
  // 导出为 WebP 格式
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

/**
 * 关闭裁剪对话框
 *
 * 触发 close 事件，通知父组件关闭。
 */
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
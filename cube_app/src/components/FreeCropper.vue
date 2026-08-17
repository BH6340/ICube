<script setup>
/**
 * FreeCropper.vue — 自由矩形裁剪组件
 *
 * 用户在图片上拖拽绘制矩形区域，可拖动四角调整大小，拖动中间移动位置。
 * 用于 OCR 识别前选择公式文字区域。
 */
defineOptions({ name: 'FreeCropper' })

const props = defineProps({
  src: { type: String, required: true },
})
const emit = defineEmits(['confirm', 'cancel'])

const containerEl = ref(null)
const imgEl = ref(null)
const imgLoaded = ref(false)
const naturalWidth = ref(0)
const naturalHeight = ref(0)

// 图片在容器中的实际显示位置和尺寸（object-fit: contain）
const dispX = ref(0)
const dispY = ref(0)
const dispW = ref(0)
const dispH = ref(0)

// 裁剪框（容器坐标）
const crop = ref({ x: 0, y: 0, w: 0, h: 0 })
const hasCrop = ref(false)

let mode = '' // 'draw' | 'move' | 'resize-tl' | 'resize-tr' | 'resize-bl' | 'resize-br'
let startX = 0
let startY = 0
let cropStart = { x: 0, y: 0, w: 0, h: 0 }

function onImgLoad(e) {
  const img = e.target
  naturalWidth.value = img.naturalWidth
  naturalHeight.value = img.naturalHeight
  calculateLayout()
  // 初始裁剪框：居中 80%
  const cw = containerEl.value.clientWidth
  const ch = containerEl.value.clientHeight
  const w = dispW.value * 0.8
  const h = dispH.value * 0.4
  crop.value = {
    x: dispX.value + (dispW.value - w) / 2,
    y: dispY.value + (dispH.value - h) / 2,
    w,
    h,
  }
  hasCrop.value = true
  imgLoaded.value = true
}

function calculateLayout() {
  const container = containerEl.value
  if (!container) return
  const cw = container.clientWidth
  const ch = container.clientHeight
  const iw = naturalWidth.value
  const ih = naturalHeight.value
  const containerRatio = cw / ch
  const imgRatio = iw / ih

  if (imgRatio > containerRatio) {
    dispW.value = cw
    dispH.value = cw / imgRatio
    dispX.value = 0
    dispY.value = (ch - dispH.value) / 2
  } else {
    dispH.value = ch
    dispW.value = ch * imgRatio
    dispX.value = (cw - dispW.value) / 2
    dispY.value = 0
  }
}

function getTouchPos(e) {
  const rect = containerEl.value.getBoundingClientRect()
  const t = e.touches ? e.touches[0] : e
  return { x: t.clientX - rect.left, y: t.clientY - rect.top }
}

function hitTest(pos) {
  if (!hasCrop.value) return 'draw'
  const c = crop.value
  const handleSize = 24
  const corners = {
    'resize-tl': { x: c.x, y: c.y },
    'resize-tr': { x: c.x + c.w, y: c.y },
    'resize-bl': { x: c.x, y: c.y + c.h },
    'resize-br': { x: c.x + c.w, y: c.y + c.h },
  }
  for (const [key, p] of Object.entries(corners)) {
    if (Math.abs(pos.x - p.x) < handleSize && Math.abs(pos.y - p.y) < handleSize) {
      return key
    }
  }
  if (pos.x >= c.x && pos.x <= c.x + c.w && pos.y >= c.y && pos.y <= c.y + c.h) {
    return 'move'
  }
  return 'draw'
}

function clampCrop(c) {
  const minX = dispX.value
  const maxX = dispX.value + dispW.value
  const minY = dispY.value
  const maxY = dispY.value + dispH.value
  c.x = Math.max(minX, Math.min(maxX - c.w, c.x))
  c.y = Math.max(minY, Math.min(maxY - c.h, c.y))
  c.w = Math.max(20, Math.min(maxX - c.x, c.w))
  c.h = Math.max(20, Math.min(maxY - c.y, c.h))
  return c
}

function onTouchStart(e) {
  const pos = getTouchPos(e)
  mode = hitTest(pos)
  startX = pos.x
  startY = pos.y
  cropStart = { ...crop.value }

  if (mode === 'draw') {
    crop.value = { x: pos.x, y: pos.y, w: 0, h: 0 }
    hasCrop.value = false
  }
}

function onTouchMove(e) {
  e.preventDefault()
  const pos = getTouchPos(e)
  const dx = pos.x - startX
  const dy = pos.y - startY

  if (mode === 'draw') {
    const x = Math.min(startX, pos.x)
    const y = Math.min(startY, pos.y)
    const w = Math.abs(dx)
    const h = Math.abs(dy)
    crop.value = clampCrop({ x, y, w, h })
    if (w > 10 && h > 10) hasCrop.value = true
  } else if (mode === 'move') {
    crop.value = clampCrop({
      x: cropStart.x + dx,
      y: cropStart.y + dy,
      w: cropStart.w,
      h: cropStart.h,
    })
  } else if (mode.startsWith('resize-')) {
    let { x, y, w, h } = cropStart
    if (mode.includes('l')) { x = cropStart.x + dx; w = cropStart.w - dx }
    if (mode.includes('r')) { w = cropStart.w + dx }
    if (mode.includes('t')) { y = cropStart.y + dy; h = cropStart.h - dy }
    if (mode.includes('b')) { h = cropStart.h + dy }
    // 处理负宽高（拖过对角线）
    if (w < 0) { x += w; w = -w }
    if (h < 0) { y += h; h = -h }
    crop.value = clampCrop({ x, y, w, h })
  }
}

function onTouchEnd() {
  mode = ''
}

function confirmCrop() {
  const c = crop.value
  const scaleX = naturalWidth.value / dispW.value
  const scaleY = naturalHeight.value / dispH.value
  emit('confirm', {
    x: Math.round((c.x - dispX.value) * scaleX),
    y: Math.round((c.y - dispY.value) * scaleY),
    width: Math.round(c.w * scaleX),
    height: Math.round(c.h * scaleY),
  })
}
</script>

<template>
  <div class="cropper-overlay">
    <div
      class="cropper-image-area"
      ref="containerEl"
      @touchstart.passive="onTouchStart"
      @touchmove="onTouchMove"
      @touchend.passive="onTouchEnd"
    >
      <img
        ref="imgEl"
        :src="src"
        class="cropper-img"
        @load="onImgLoad"
      />
      <template v-if="imgLoaded">
        <!-- 遮罩 -->
        <div class="mask" :style="{
          clipPath: `polygon(0 0, 100% 0, 100% 100%, 0 100%, 0 0, ${crop.x}px ${crop.y}px, ${crop.x + crop.w}px ${crop.y}px, ${crop.x + crop.w}px ${crop.y + crop.h}px, ${crop.x}px ${crop.y + crop.h}px, ${crop.x}px ${crop.y}px)`
        }"></div>

        <!-- 裁剪框 -->
        <div
          v-if="hasCrop"
          class="crop-rect"
          :style="{ left: crop.x + 'px', top: crop.y + 'px', width: crop.w + 'px', height: crop.h + 'px' }"
        >
          <div class="handle handle-tl"></div>
          <div class="handle handle-tr"></div>
          <div class="handle handle-bl"></div>
          <div class="handle handle-br"></div>
        </div>

        <div v-if="!hasCrop" class="draw-hint">拖拽选择公式区域</div>
      </template>
    </div>

    <div class="cropper-actions">
      <van-button plain block @click="emit('cancel')">取消</van-button>
      <van-button type="primary" block :disabled="!hasCrop" @click="confirmCrop">确认裁剪</van-button>
    </div>
  </div>
</template>

<style scoped>
.cropper-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #000;
  display: flex;
  flex-direction: column;
}

.cropper-image-area {
  flex: 1;
  position: relative;
  overflow: hidden;
  touch-action: none;
}

.cropper-img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  user-select: none;
  -webkit-user-select: none;
  pointer-events: none;
}

.mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  pointer-events: none;
}

.crop-rect {
  position: absolute;
  border: 2px solid #fff;
  box-sizing: border-box;
  pointer-events: none;
}

.handle {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 3px solid #fff;
  background: rgba(25, 137, 250, 0.5);
  border-radius: 50%;
}

.handle-tl { top: -10px; left: -10px; }
.handle-tr { top: -10px; right: -10px; }
.handle-bl { bottom: -10px; left: -10px; }
.handle-br { bottom: -10px; right: -10px; }

.draw-hint {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  pointer-events: none;
}

.cropper-actions {
  display: flex;
  gap: 12px;
  padding: 16px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
  background: #000;
}

.cropper-actions .van-button {
  flex: 1;
}
</style>

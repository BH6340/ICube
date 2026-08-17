<script setup>
/**
 * ImageCropper.vue — 通用图片裁剪组件
 *
 * 固定 1:1 裁剪框居中，支持双指缩放和单指拖拽图片。
 */
defineOptions({ name: 'ImageCropper' })

const props = defineProps({
  src: { type: String, required: true },
})
const emit = defineEmits(['confirm', 'cancel'])

const containerEl = ref(null)
const imgLoaded = ref(false)
const naturalWidth = ref(0)
const naturalHeight = ref(0)

// 基础布局（fit: contain 后的尺寸和位置）
const baseW = ref(0)
const baseH = ref(0)
const baseOffsetX = ref(0)
const baseOffsetY = ref(0)

// 缩放和平移
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)

// 裁剪框（固定居中）
const cropSize = ref(0)
const cropLeft = ref(0)
const cropTop = ref(0)

// 计算后的图片显示尺寸和位置
const dispW = computed(() => baseW.value * scale.value)
const dispH = computed(() => baseH.value * scale.value)
const imgLeft = computed(() => baseOffsetX.value + panX.value)
const imgTop = computed(() => baseOffsetY.value + panY.value)

const imgStyle = computed(() => ({
  position: 'absolute',
  left: imgLeft.value + 'px',
  top: imgTop.value + 'px',
  width: dispW.value + 'px',
  height: dispH.value + 'px',
}))

function onImgLoad(e) {
  const img = e.target
  naturalWidth.value = img.naturalWidth
  naturalHeight.value = img.naturalHeight
  calculateLayout()
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
    baseW.value = cw
    baseH.value = cw / imgRatio
    baseOffsetX.value = 0
    baseOffsetY.value = (ch - baseH.value) / 2
  } else {
    baseH.value = ch
    baseW.value = ch * imgRatio
    baseOffsetX.value = (cw - baseW.value) / 2
    baseOffsetY.value = 0
  }

  cropSize.value = Math.min(baseW.value, baseH.value) * 0.85
  cropLeft.value = (cw - cropSize.value) / 2
  cropTop.value = (ch - cropSize.value) / 2

  scale.value = 1
  panX.value = 0
  panY.value = 0
}

function clampPan() {
  const minX = cropLeft.value + cropSize.value - baseOffsetX.value - dispW.value
  const maxX = cropLeft.value - baseOffsetX.value
  const minY = cropTop.value + cropSize.value - baseOffsetY.value - dispH.value
  const maxY = cropTop.value - baseOffsetY.value
  panX.value = Math.max(minX, Math.min(maxX, panX.value))
  panY.value = Math.max(minY, Math.min(maxY, panY.value))
}

// ─── 手势处理 ──────────────────────────────
let mode = '' // 'pan' | 'pinch' | ''
let panStartX = 0
let panStartY = 0
let panOriginX = 0
let panOriginY = 0
let pinchStartDist = 0
let pinchStartScale = 1

function getTouchDist(touches) {
  const dx = touches[0].clientX - touches[1].clientX
  const dy = touches[0].clientY - touches[1].clientY
  return Math.hypot(dx, dy)
}

function onTouchStart(e) {
  if (e.touches.length === 1) {
    mode = 'pan'
    panStartX = e.touches[0].clientX
    panStartY = e.touches[0].clientY
    panOriginX = panX.value
    panOriginY = panY.value
  } else if (e.touches.length === 2) {
    mode = 'pinch'
    pinchStartDist = getTouchDist(e.touches)
    pinchStartScale = scale.value
  }
}

function onTouchMove(e) {
  if (mode === 'pan' && e.touches.length === 1) {
    e.preventDefault()
    panX.value = panOriginX + (e.touches[0].clientX - panStartX)
    panY.value = panOriginY + (e.touches[0].clientY - panStartY)
    clampPan()
  } else if (mode === 'pinch' && e.touches.length === 2) {
    e.preventDefault()
    const dist = getTouchDist(e.touches)
    const newScale = pinchStartScale * (dist / pinchStartDist)
    scale.value = Math.max(1, Math.min(5, newScale))
    clampPan()
  }
}

function onTouchEnd() {
  mode = ''
}

function confirmCrop() {
  const scaleFactor = naturalWidth.value / dispW.value
  const relX = cropLeft.value - imgLeft.value
  const relY = cropTop.value - imgTop.value
  emit('confirm', {
    x: Math.round(relX * scaleFactor),
    y: Math.round(relY * scaleFactor),
    width: Math.round(cropSize.value * scaleFactor),
    height: Math.round(cropSize.value * scaleFactor),
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
        :src="src"
        :style="imgStyle"
        @load="onImgLoad"
      />
      <template v-if="imgLoaded">
        <!-- 遮罩 -->
        <div class="mask-block" :style="{ left: 0, top: 0, width: '100%', height: cropTop + 'px' }"></div>
        <div class="mask-block" :style="{ left: 0, top: (cropTop + cropSize) + 'px', width: '100%', height: 'calc(100% - ' + (cropTop + cropSize) + 'px)' }"></div>
        <div class="mask-block" :style="{ left: 0, top: cropTop + 'px', width: cropLeft + 'px', height: cropSize + 'px' }"></div>
        <div class="mask-block" :style="{ left: (cropLeft + cropSize) + 'px', top: cropTop + 'px', width: 'calc(100% - ' + (cropLeft + cropSize) + 'px)', height: cropSize + 'px' }"></div>

        <!-- 裁剪框 -->
        <div
          class="crop-box"
          :style="{ left: cropLeft + 'px', top: cropTop + 'px', width: cropSize + 'px', height: cropSize + 'px' }"
        >
          <div class="crop-grid-h" style="top: 33.33%"></div>
          <div class="crop-grid-h" style="top: 66.66%"></div>
          <div class="crop-grid-v" style="left: 33.33%"></div>
          <div class="crop-grid-v" style="left: 66.66%"></div>
          <div class="crop-corner tl"></div>
          <div class="crop-corner tr"></div>
          <div class="crop-corner bl"></div>
          <div class="crop-corner br"></div>
        </div>

        <div class="zoom-hint">双指缩放 · 单指拖动</div>
      </template>
    </div>

    <div class="cropper-actions">
      <van-button plain block @click="emit('cancel')">取消</van-button>
      <van-button type="primary" block @click="confirmCrop">确认裁剪</van-button>
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

.cropper-image-area img {
  user-select: none;
  -webkit-user-select: none;
  pointer-events: none;
  max-width: none;
  max-height: none;
}

.mask-block {
  position: absolute;
  background: rgba(0, 0, 0, 0.55);
  pointer-events: none;
}

.crop-box {
  position: absolute;
  border: 2px solid #fff;
  box-sizing: border-box;
  pointer-events: none;
}

.crop-grid-h {
  position: absolute;
  left: 0;
  width: 100%;
  height: 1px;
  background: rgba(255, 255, 255, 0.3);
}

.crop-grid-v {
  position: absolute;
  top: 0;
  width: 1px;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
}

.crop-corner {
  position: absolute;
  width: 16px;
  height: 16px;
  border: 3px solid #fff;
}

.crop-corner.tl { top: -2px; left: -2px; border-right: none; border-bottom: none; }
.crop-corner.tr { top: -2px; right: -2px; border-left: none; border-bottom: none; }
.crop-corner.bl { bottom: -2px; left: -2px; border-right: none; border-top: none; }
.crop-corner.br { bottom: -2px; right: -2px; border-left: none; border-top: none; }

.zoom-hint {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.75rem;
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

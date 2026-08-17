/**
 * 图片压缩工具
 * 基于 Canvas 实现裁剪和压缩，输出 webp 格式
 */

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })
}

/**
 * 获取图片自然尺寸
 * @param {File|Blob|string} source - File 对象或 DataURL
 * @returns {Promise<{width: number, height: number}>}
 */
export async function getImageSize(source) {
  const src = typeof source === 'string' ? source : URL.createObjectURL(source)
  const img = await loadImage(src)
  const result = { width: img.naturalWidth, height: img.naturalHeight }
  if (typeof source !== 'string') URL.revokeObjectURL(src)
  return result
}

/**
 * 裁剪并压缩图片
 * @param {File|Blob|string} source - File 对象或 DataURL
 * @param {Object} crop - 裁剪区域 { x, y, width, height }（基于原图坐标）
 * @param {Object} options
 * @param {number} options.outputSize - 输出边长（默认 512）
 * @param {number} options.quality - 压缩质量 0-1（默认 0.85）
 * @param {string} options.mimeType - 输出格式（默认 image/webp）
 * @returns {Promise<File>}
 */
export async function cropAndCompress(source, crop, options = {}) {
  const { outputSize = 512, quality = 0.85, mimeType = 'image/webp' } = options

  const src = typeof source === 'string' ? source : URL.createObjectURL(source)
  const img = await loadImage(src)

  const canvas = document.createElement('canvas')
  canvas.width = outputSize
  canvas.height = outputSize
  const ctx = canvas.getContext('2d')
  ctx.drawImage(
    img,
    crop.x, crop.y, crop.width, crop.height,
    0, 0, outputSize, outputSize
  )

  if (typeof source !== 'string') URL.revokeObjectURL(src)

  const blob = await new Promise(resolve => canvas.toBlob(resolve, mimeType, quality))
  const ext = mimeType === 'image/webp' ? 'webp' : 'jpg'
  return new File([blob], `upload.${ext}`, { type: mimeType })
}

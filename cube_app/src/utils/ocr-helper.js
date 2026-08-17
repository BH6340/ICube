/**
 * ocr-helper.js — OCR 识别辅助工具
 *
 * 优化项：
 * 1. 自适应预处理（干净图跳过强预处理）
 * 2. 多轮 PSM 识别取最优
 * 3. 投影分割字符级识别（防止撇号粘连）
 * 4. 字符映射修正（H→'、W→删除）
 * 5. 清洗后按有效 token 数 × 置信度评分
 */

function otsuThreshold(grayData) {
  const histogram = new Array(256).fill(0)
  for (let i = 0; i < grayData.length; i++) {
    histogram[grayData[i]]++
  }
  const total = grayData.length
  let sumAll = 0
  for (let i = 0; i < 256; i++) sumAll += i * histogram[i]

  let sumBg = 0, weightBg = 0, maxVariance = 0, bestThreshold = 0
  for (let t = 0; t < 256; t++) {
    weightBg += histogram[t]
    if (weightBg === 0) continue
    const weightFg = total - weightBg
    if (weightFg === 0) break
    sumBg += t * histogram[t]
    const meanBg = sumBg / weightBg
    const meanFg = (sumAll - sumBg) / weightFg
    const variance = weightBg * weightFg * (meanBg - meanFg) ** 2
    if (variance > maxVariance) {
      maxVariance = variance
      bestThreshold = t
    }
  }
  return bestThreshold
}

function dilate(canvas, iterations = 1) {
  const ctx = canvas.getContext('2d')
  for (let iter = 0; iter < iterations; iter++) {
    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const src = imgData.data
    const dst = new Uint8ClampedArray(src.length)
    const w = canvas.width, h = canvas.height
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const idx = (y * w + x) * 4
        let max = 0
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const nx = x + dx, ny = y + dy
            if (nx >= 0 && nx < w && ny >= 0 && ny < h) {
              const nidx = (ny * w + nx) * 4
              if (src[nidx] > max) max = src[nidx]
            }
          }
        }
        dst[idx] = dst[idx + 1] = dst[idx + 2] = max
        dst[idx + 3] = 255
      }
    }
    ctx.putImageData(new ImageData(dst, w, h), 0, 0)
  }
}

function isCleanBinaryImage(grayValues) {
  let binaryCount = 0
  for (const g of grayValues) {
    if (g < 30 || g > 225) binaryCount++
  }
  return binaryCount / grayValues.length > 0.9
}

function padCanvas(canvas, pw, ph) {
  const padSize = Math.max(20, Math.round(pw * 0.1))
  const paddedCanvas = document.createElement('canvas')
  paddedCanvas.width = pw + padSize * 2
  paddedCanvas.height = ph + padSize * 2
  const paddedCtx = paddedCanvas.getContext('2d')
  paddedCtx.fillStyle = '#ffffff'
  paddedCtx.fillRect(0, 0, paddedCanvas.width, paddedCanvas.height)
  paddedCtx.drawImage(canvas, padSize, padSize)
  return paddedCanvas
}

export function preprocessImage(cropCanvas, opts = {}) {
  const { scale = 4, contrast = 2.0, useDilate = true, usePad = true } = opts

  const pw = cropCanvas.width * scale
  const ph = cropCanvas.height * scale
  const procCanvas = document.createElement('canvas')
  procCanvas.width = pw
  procCanvas.height = ph
  const procCtx = procCanvas.getContext('2d')
  procCtx.imageSmoothingEnabled = true
  procCtx.imageSmoothingQuality = 'high'
  procCtx.drawImage(cropCanvas, 0, 0, pw, ph)

  const probeData = procCtx.getImageData(0, 0, pw, ph).data
  const probeGray = []
  for (let i = 0; i < probeData.length; i += 4) {
    probeGray.push(probeData[i] * 0.299 + probeData[i + 1] * 0.587 + probeData[i + 2] * 0.114)
  }

  if (isCleanBinaryImage(probeGray)) {
    return usePad ? padCanvas(procCanvas, pw, ph) : procCanvas
  }

  const imgData = procCtx.getImageData(0, 0, pw, ph)
  const data = imgData.data
  const grayValues = []
  for (let i = 0; i < data.length; i += 4) {
    const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114
    let val = ((gray / 255 - 0.5) * contrast + 0.5) * 255
    val = Math.max(0, Math.min(255, val))
    grayValues.push(Math.round(val))
  }

  const threshold = otsuThreshold(grayValues)
  for (let i = 0, j = 0; i < data.length; i += 4, j++) {
    const val = grayValues[j] < threshold ? 0 : 255
    data[i] = data[i + 1] = data[i + 2] = val
    data[i + 3] = 255
  }
  procCtx.putImageData(imgData, 0, 0)

  if (useDilate) {
    dilate(procCanvas, 1)
  }

  return usePad ? padCanvas(procCanvas, pw, ph) : procCanvas
}

/**
 * 投影分割字符级识别
 * 1. 行投影分割出每一行
 * 2. 列投影分割出每个字符/字符组
 * 3. 用 PSM 10（单字符模式）逐个识别
 * 优势：防止撇号 ' 与相邻字母粘连
 */
async function segmentAndRecognize(canvas, Tesseract) {
  const ctx = canvas.getContext('2d')
  const w = canvas.width, h = canvas.height
  const imgData = ctx.getImageData(0, 0, w, h)
  const data = imgData.data

  const binary = new Uint8Array(w * h)
  for (let i = 0, j = 0; i < data.length; i += 4, j++) {
    const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114
    binary[j] = gray < 128 ? 1 : 0
  }

  // 行投影
  const rowHist = new Array(h).fill(0)
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      rowHist[y] += binary[y * w + x]
    }
  }

  const rows = []
  let inRow = false, rowStart = 0
  for (let y = 0; y < h; y++) {
    if (rowHist[y] >= 2) {
      if (!inRow) { inRow = true; rowStart = y }
    } else {
      if (inRow) { rows.push({ start: rowStart, end: y - 1 }); inRow = false }
    }
  }
  if (inRow) rows.push({ start: rowStart, end: h - 1 })

  let fullText = ''

  for (const row of rows) {
    const rowH = row.end - row.start + 1

    // 列投影
    const colHist = new Array(w).fill(0)
    for (let x = 0; x < w; x++) {
      for (let y = row.start; y <= row.end; y++) {
        colHist[x] += binary[y * w + x]
      }
    }

    const chars = []
    let inChar = false, charStart = 0
    for (let x = 0; x < w; x++) {
      if (colHist[x] >= 1) {
        if (!inChar) { inChar = true; charStart = x }
      } else {
        if (inChar) { chars.push({ start: charStart, end: x - 1 }); inChar = false }
      }
    }
    if (inChar) chars.push({ start: charStart, end: w - 1 })

    for (const char of chars) {
      const charW = char.end - char.start + 1
      if (charW < 3) continue
      const pad = 15
      const charCanvas = document.createElement('canvas')
      charCanvas.width = charW + pad * 2
      charCanvas.height = rowH + pad * 2
      const charCtx = charCanvas.getContext('2d')
      charCtx.fillStyle = '#ffffff'
      charCtx.fillRect(0, 0, charCanvas.width, charCanvas.height)
      charCtx.drawImage(canvas, char.start, row.start, charW, rowH, pad, pad, charW, rowH)

      const dataUrl = charCanvas.toDataURL('image/png')
      const r = await Tesseract.recognize(dataUrl, 'eng', {
        tessedit_char_whitelist: "RLUDFBMESxyzrludfb'2",
        tessedit_pageseg_mode: '10',
        tessedit_ocr_engine_mode: '2',
      })
      fullText += r.data.text.trim()
    }

    fullText += '\n'
  }

  return fullText
}

export async function multiPassOCR(dataUrl, rawCanvas) {
  const { default: Tesseract } = await import('tesseract.js')
  const psmModes = ['7', '8', '13', '6']
  const passes = []

  for (const psm of psmModes) {
    const result = await Tesseract.recognize(dataUrl, 'eng', {
      tessedit_char_whitelist: "RLUDFBMESxyzrludfb'2() ",
      tessedit_pageseg_mode: psm,
      tessedit_ocr_engine_mode: '2',
      preserve_interword_spaces: '1',
      user_defined_dpi: '300',
    })
    const cleaned = cleanNotation(result.data.text)
    const validTokens = countValidTokens(result.data.text)
    const score = result.data.confidence * Math.max(1, validTokens)
    passes.push({
      text: result.data.text,
      confidence: result.data.confidence,
      psm,
      cleaned,
      validTokens,
      score,
    })
  }

  if (rawCanvas) {
    try {
      const segText = await segmentAndRecognize(rawCanvas, Tesseract)
      const cleaned = cleanNotation(segText)
      const validTokens = countValidTokens(segText)
      const score = 80 * Math.max(1, validTokens)
      passes.push({
        text: segText,
        confidence: 80,
        psm: 'seg',
        cleaned,
        validTokens,
        score,
      })
    } catch (e) {
      console.warn('segmentAndRecognize failed:', e)
    }
  }

  passes.sort((a, b) => b.score - a.score)
  return passes[0]
}

function cleanNotation(text) {
  let cleaned = text.replace(/[′ʼ`´’]/g, "'")
  // 撇号 ' 的常见误认：H、/、|、I
  cleaned = cleaned.replace(/[/|]/g, "'")
  cleaned = cleaned.replace(/H/g, "'")
  // 小写 r 的常见误认：I（大写i）
  cleaned = cleaned.replace(/I/g, 'r')
  // W 是括号 ( 被误认的结果，直接删除
  cleaned = cleaned.replace(/W/g, ' ')
  // 删除所有括号（英文+中文）和换行
  cleaned = cleaned.replace(/[()（［【〕】｝〉>]/g, ' ')
  cleaned = cleaned.replace(/[\n\r]/g, ' ')
  // 分割粘连 token
  const rawTokens = cleaned.split(/[\s,]+/).filter(Boolean)
  const tokens = []
  for (const t of rawTokens) {
    if (t.length <= 2) {
      tokens.push(t)
    } else {
      let i = 0
      while (i < t.length) {
        if (i + 1 < t.length && (t[i + 1] === "'" || t[i + 1] === "2")) {
          tokens.push(t[i] + t[i + 1])
          i += 2
        } else {
          tokens.push(t[i])
          i += 1
        }
      }
    }
  }
  const validPattern = /^[RLUDFBMESxyzrludfb]['2]?$/
  return tokens.filter(t => validPattern.test(t)).join(' ')
}

function countValidTokens(text) {
  return cleanNotation(text).split(' ').filter(Boolean).length
}

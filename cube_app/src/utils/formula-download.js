/**
 * 公式下载到本地工具
 * 基于 localStorage 存储已下载的公式数据
 */

const STORAGE_KEY = 'downloaded_formulas'

function loadList() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

function saveList(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

export function getDownloadedFormulas() {
  return loadList()
}

export function getDownloadedIds() {
  return new Set(loadList().map(f => f.id))
}

export function isDownloaded(formulaId) {
  return loadList().some(f => f.id === formulaId)
}

export function downloadFormula(formula) {
  const list = loadList()
  if (list.some(f => f.id === formula.id)) return false
  list.push({
    id: formula.id,
    name: formula.name,
    notation: formula.notation,
    thumbnail: formula.thumbnail || '',
    difficulty: formula.difficulty,
    category_name: formula.category?.name || formula.category_name || '',
    author_name: formula.author?.username || formula.author_username || '',
    downloaded_at: Date.now(),
  })
  saveList(list)
  return true
}

export function removeDownload(formulaId) {
  const list = loadList().filter(f => f.id !== formulaId)
  saveList(list)
}

export function batchDownload(formulas) {
  const existing = new Set(loadList().map(f => f.id))
  let added = 0
  const list = loadList()
  for (const formula of formulas) {
    if (existing.has(formula.id)) continue
    list.push({
      id: formula.id,
      name: formula.name,
      notation: formula.notation,
      thumbnail: formula.thumbnail || '',
      difficulty: formula.difficulty,
      category_name: formula.category?.name || formula.category_name || '',
      author_name: formula.author?.username || formula.author_username || '',
      downloaded_at: Date.now(),
    })
    existing.add(formula.id)
    added++
  }
  saveList(list)
  return added
}

export function getDownloadCount() {
  return loadList().length
}

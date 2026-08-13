/**
 * 媒体 URL 拼接工具
 *
 * 后端返回的图片路径为相对路径（如 /media/avatars/xxx.jpg）。
 * 开发环境靠 Vite proxy 的 /media 转发；生产环境 WebView 中
 * origin 是 https://localhost，/media/ 无法访问后端文件，需拼接完整域名。
 */

const MEDIA_BASE = import.meta.env.VITE_MEDIA_BASE_URL || ''

/**
 * 将相对媒体路径转为完整 URL
 *
 * @param {string|*} path - 后端返回的媒体路径
 * @returns {string} 完整 URL（开发时返回相对路径，生产时返回带域名的完整 URL）
 */
export function buildMediaUrl(path) {
    if (!path) return ''
    if (typeof path !== 'string') path = String(path)
    // 已是完整 URL，直接返回
    if (path.startsWith('http')) return path
    // 确保以 / 开头
    const cleanPath = path.startsWith('/') ? path : `/${path}`
    return `${MEDIA_BASE}${cleanPath}`
}

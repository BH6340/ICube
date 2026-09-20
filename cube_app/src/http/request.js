/**
 * HTTP 请求封装模块（移动端版）
 *
 * 基于 cube_front/src/http/request.js 改造：
 *   - baseURL: 改为环境变量（开发走 proxy，生产走真实域名）
 *   - 错误提示: ElMessage → Vant showToast
 *   - 其余逻辑不变：Token 注入、code===100 判断、401 清除登录态、防抖 3s
 */

import axios from 'axios'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'

/**
 * 错误提示防抖缓存：key=消息内容，value=上次提示的时间戳
 * 3 秒内相同的错误消息只弹一次，避免并发多请求失败时刷屏
 */
const lastErrorMap = new Map()
const ERROR_DEBOUNCE_MS = 3000

/**
 * 统一弹错误提示，带防抖
 */
function showErrorMsg(message) {
    const now = Date.now()
    const lastAt = lastErrorMap.get(message)
    if (lastAt && now - lastAt < ERROR_DEBOUNCE_MS) return
    lastErrorMap.set(message, now)
    showToast({
        type: 'fail',
        message,
        position: 'top',
    })
}

/**
 * 生产环境后端地址（APP WebView 中使用）
 * 不依赖环境变量，直接硬编码，确保构建产物中一定有正确地址
 */
const PROD_API_BASE = 'http://8.136.100.251'

/**
 * 运行时确定 baseURL：
 *   - file:// 协议（APP WebView）：用 PROD_API_BASE 直接请求后端
 *   - http/https 协议（浏览器开发/预览）：空字符串走相对路径 + Vite proxy
 */
function resolveBaseURL() {
    if (typeof window !== 'undefined' && window.location?.protocol === 'file:') {
        return PROD_API_BASE
    }
    return import.meta.env.VITE_API_BASE_URL || ''
}

/**
 * 创建 Axios 实例
 */
const service = axios.create({
    baseURL: resolveBaseURL(),
    timeout: 10000
})

/**
 * 请求拦截器
 *
 * Token 格式：`Token ${token}`（与后端 CachedJWTAuthentication 兼容）
 */
service.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers['Authorization'] = `Token ${token}`
        }
        // APP WebView 的默认 User-Agent 可能被阿里云 WAF/DDoS 拦截
        // 强制使用与手机浏览器一致的 UA，绕过检测
        if (typeof navigator !== 'undefined' && navigator.userAgent) {
            config.headers['User-Agent'] = navigator.userAgent
        }
        // 统一补尾斜杠：Django APPEND_SLASH 对 POST 请求无法自动重定向，
        // 缺少尾斜杠会直接 500。无 query 且不以 / 结尾的 /api/ 路径补 /
        if (config.url && config.url.startsWith('/api/')) {
            const [path, query] = config.url.split('?')
            if (path && !path.endsWith('/')) {
                config.url = query ? `${path}/?${query}` : `${path}/`
            }
        }
        return config
    },
    error => Promise.reject(error)
)

/**
 * 响应拦截器
 *
 *   - 业务成功：code === 100，直接返回响应数据
 *   - 业务失败：code !== 100，显示错误消息并返回 Promise.reject
 *   - HTTP 错误：4xx/5xx，提取后端错误信息并显示
 *   - 401 且已有 Token：清除登录态（Token 失效）
 */
service.interceptors.response.use(
    response => {
        const res = response.data

        if (res.code !== 100) {
            showErrorMsg(!res.msg ? '请求服务器异常,请联系管理员' : res.msg)
            return Promise.reject(new Error(res.msg || 'Error'))
        } else {
            return res
        }
    },
    error => {
        const status = error.response?.status
        const responseData = error.response?.data
        const hadToken = Boolean(localStorage.getItem('token'))

        if (status === 401 && hadToken) {
            useUserStore().clearInfo()
        }

        const errorMsg = responseData?.msg
            || (status === 401
                ? (hadToken ? '登录已失效，请重新登录' : '请先登录')
                : responseData?.detail)
            || '请求服务器异常,请联系管理员'

        showErrorMsg(errorMsg)
        return Promise.reject(error)
    }
)

export default service

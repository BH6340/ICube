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
 * 创建 Axios 实例
 *
 * baseURL 由环境变量控制：
 *   - 开发环境（.env）：空字符串，/api 经 Vite proxy 转发到 127.0.0.1:8000
 *   - 生产环境（.env.production）：真实域名，WebView 中直接请求后端
 */
const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
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

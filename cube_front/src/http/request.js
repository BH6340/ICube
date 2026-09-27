/**
 * HTTP 请求封装模块
 *
 * 基于 Axios 封装的统一请求模块，包含：
 *   - 请求拦截器：自动注入 Token
 *   - 响应拦截器：统一错误处理、业务逻辑判断、401 自动刷新
 *   - 全局错误提示：使用 Element Plus 的 ElMessage
 *
 * 设计特点：
 *   - **Token 自动注入**：从 localStorage 获取 Token 并添加到请求头
 *   - **统一响应格式**：后端返回 code 为 100 表示成功，其他为业务错误
 *   - **无感刷新**：401 时自动用 refresh_token 换新 token 并重试原请求
 *   - **防并发刷新**：多个请求同时 401 时只刷新一次，其他请求排队等待
 *   - **错误分层处理**：HTTP 错误和业务错误分开处理
 *   - **Promise 链式传递**：业务错误返回 Promise.reject，便于组件 try-catch 捕获
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { refreshTokenApi } from '@/api/user'

/**
 * 错误提示防抖缓存：key=消息内容，value=上次提示的时间戳
 * 3 秒内相同的错误消息只弹一次，避免并发多请求失败时刷屏
 */
const lastErrorMap = new Map()
const ERROR_DEBOUNCE_MS = 3000

/**
 * 统一弹错误提示，带防抖和 Element Plus grouping 合并
 */
function showErrorMsg(message) {
  const now = Date.now()
  const lastAt = lastErrorMap.get(message)
  if (lastAt && now - lastAt < ERROR_DEBOUNCE_MS) return
  lastErrorMap.set(message, now)
  ElMessage({
    type: 'error',
    message,
    grouping: true,
  })
}

/**
 * 创建 Axios 实例
 *
 * 配置说明：
 *   - baseURL: 空字符串，由 Vite 代理配置处理（开发环境代理到 /api）
 *   - timeout: 请求超时时间 10000ms（原 5000ms 在网速稍慢时容易误报超时）
 */
const service = axios.create({
  baseURL: '',
  timeout: 10000,
})

/**
 * 请求拦截器
 *
 * 在请求发送前自动注入 Token，实现无感知认证。
 * Token 格式：`Token ${token}`（与后端 CachedJWTAuthentication 兼容）
 */
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Token ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * 防并发刷新状态
 *
 * - isRefreshing: 是否正在刷新 Token
 * - refreshSubscribers: 等待刷新完成的请求队列，刷新成功后依次重试
 */
let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb)
}

function onRefreshed(token) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

/**
 * 响应拦截器
 *
 * 统一处理响应数据和错误：
 *   - 业务成功：code === 100，直接返回响应数据
 *   - 业务失败：code !== 100，显示错误消息并返回 Promise.reject
 *   - HTTP 401：有 token 时尝试自动刷新，无 token 提示登录
 *   - 其他 HTTP 错误：提取后端错误信息并显示
 */
service.interceptors.response.use(
  (response) => {
    const res = response.data

    // 业务逻辑错误判断
    if (res.code !== 100) {
      showErrorMsg(!res.msg ? '请求服务器异常,请联系管理员' : res.msg)
      return Promise.reject(new Error(res.msg || 'Error'))
    } else {
      return res
    }
  },
  async (error) => {
    const status = error.response?.status
    const responseData = error.response?.data
    const hadToken = Boolean(localStorage.getItem('token'))
    const config = error.config

    // 401 且有 token 且不是刷新请求本身 → 尝试自动刷新
    if (status === 401 && hadToken && !config?.skipAuthRefresh) {
      const refreshTok = localStorage.getItem('refresh_token')

      if (!refreshTok) {
        // 没有 refresh_token，直接登出
        useUserStore().clearInfo()
        showErrorMsg('登录已失效，请重新登录')
        return Promise.reject(error)
      }

      if (!isRefreshing) {
        isRefreshing = true
        try {
          const res = await refreshTokenApi(refreshTok)
          const newToken = res.token
          const newRefresh = res.refresh_token

          // 更新 store 和 localStorage
          useUserStore().setTokens(newToken, newRefresh)

          // 通知所有排队的请求
          onRefreshed(newToken)

          // 用新 token 重试当前请求
          config.headers['Authorization'] = `Token ${newToken}`
          return service(config)
        } catch (refreshError) {
          // 刷新失败，清登录态
          useUserStore().clearInfo()
          showErrorMsg('登录已失效，请重新登录')
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      } else {
        // 正在刷新中，把请求加入队列等待
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken) => {
            config.headers['Authorization'] = `Token ${newToken}`
            resolve(service(config))
          })
        })
      }
    }

    // 无 token 的 401 或刷新请求的 401，正常提示
    if (status === 401 && !hadToken) {
      // 未登录状态的 401，不额外弹消息（由组件处理）
    } else if (status === 401 && config?.skipAuthRefresh) {
      // 刷新请求本身返回 401，错误消息已在上面处理
    } else {
      const errorMsg =
        responseData?.msg ||
        (status === 401
          ? hadToken
            ? '登录已失效，请重新登录'
            : '请先登录'
          : responseData?.detail) ||
        '请求服务器异常,请联系管理员'
      showErrorMsg(errorMsg)
    }

    return Promise.reject(error)
  }
)

export default service

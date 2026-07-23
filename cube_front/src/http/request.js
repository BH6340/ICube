/**
 * HTTP 请求封装模块
 *
 * 基于 Axios 封装的统一请求模块，包含：
 *   - 请求拦截器：自动注入 Token
 *   - 响应拦截器：统一错误处理和业务逻辑判断
 *   - 全局错误提示：使用 Element Plus 的 ElMessage
 *
 * 设计特点：
 *   - **Token 自动注入**：从 localStorage 获取 Token 并添加到请求头
 *   - **统一响应格式**：后端返回 code 为 100 表示成功，其他为业务错误
 *   - **错误分层处理**：HTTP 错误和业务错误分开处理
 *   - **Promise 链式传递**：业务错误返回 Promise.reject，便于组件 try-catch 捕获
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

/**
 * 创建 Axios 实例
 *
 * 配置说明：
 *   - baseURL: 空字符串，由 Vite 代理配置处理（开发环境代理到 /api）
 *   - timeout: 请求超时时间 5000ms
 */
const service = axios.create({
    baseURL: '',
    timeout: 5000
})

/**
 * 请求拦截器
 *
 * 在请求发送前自动注入 Token，实现无感知认证。
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
 * 统一处理响应数据和错误：
 *   - 业务成功：code === 100，直接返回响应数据
 *   - 业务失败：code !== 100，显示错误消息并返回 Promise.reject
 *   - HTTP 错误：4xx/5xx，提取后端错误信息并显示
 */
service.interceptors.response.use(
    response => {
        const res = response.data

        // 业务逻辑错误判断
        if (res.code !== 100) {
            ElMessage({
                type: 'error',
                message: !res.msg ? '请求服务器异常,请联系管理员' : res.msg
            })
            return Promise.reject(new Error(res.msg || 'Error'))
        } else {
            return res
        }
    },
    error => {
        const error_msg = error.response?.data?.msg

        ElMessage({
            type: 'error',
            message: !error_msg ? '请求服务器异常,请联系管理员' : error_msg
        })

        return Promise.reject(error)
    }
)

export default service
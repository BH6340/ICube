// src/http/request.js
import axios from 'axios'
import {ElMessage} from 'element-plus'
import {ElNotification} from 'element-plus'

const service = axios.create({
    baseURL: '', // 不要写死 http://localhost:8000
    // baseURL: 'http://localhost:8000', // 你的后端 Django/DRF 地址
    timeout: 5000
})

// 请求拦截器
service.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers['Authorization'] = `Token ${token}` // 根据后端需求调整格式
        }
        return config
    },
    error => Promise.reject(error)
)

// 响应拦截器
service.interceptors.response.use(
    response => {
        const res = response.data

        // 如果 code 不是 100，说明是业务逻辑错误（如用户已存在）
        if (res.code !== 100) {
            // 改用 Notification，更明显且带标题
            ElMessage({
                type: 'error',
                message: !res.msg ? '请求服务器异常,请联系管理员' : res.msg
            })
            // 返回一个 Promise.reject，这样组件里的 try-catch 就能捕获到，
            // 且不会继续执行跳转登录的逻辑
            return Promise.reject(new Error(res.msg || 'Error'))
        } else {
            return res
        }
    },
    error => {
        // 当 HTTP 状态码为 400, 401, 500 等时会进入这里
        console.dir(error) // 打印出来看看结构
        //
        // // 尝试从 error.response.data 中提取后端返回的业务错误信息
        const error_msg = error.response.data.msg

        ElMessage({
            type: 'error',
            message: !error_msg ? '请求服务器异常,请联系管理员' : error_msg
        })

        return Promise.reject(error)
    }
)

export default service
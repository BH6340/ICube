/**
 * 用户状态管理 Store
 *
 * 管理用户登录状态和个人信息，支持：
 *   - 完整用户信息设置（登录时）
 *   - 局部用户信息更新（修改资料时）
 *   - 用户信息清除（退出登录时）
 *
 * 状态字段：
 *   - token: 用户登录 Token
 *   - username: 用户名
 *   - bio: 个人简介
 *   - image: 头像 URL
 *
 * 设计特点：
 *   - **localStorage 持久化**：所有状态同步到 localStorage，刷新页面后保持登录状态
 *   - **局部更新**：updateInfo 方法只更新传入的字段，防止未改字段被刷成 undefined
 *   - **响应式**：使用 ref 创建响应式状态，配合 Pinia 实现全局状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
    /** 用户登录 Token */
    const token = ref(localStorage.getItem('token') || '')
    /** 用户名 */
    const username = ref(localStorage.getItem('username') || '')
    /** 个人简介 */
    const bio = ref(localStorage.getItem('bio') || '')
    /** 头像 URL */
    const image = ref(localStorage.getItem('image') || '')

    /**
     * 设置完整用户信息
     *
     * 登录成功后调用，同步更新所有字段到 localStorage。
     *
     * @param {Object} data - 用户信息对象
     * @param {string} data.token - 用户 Token
     * @param {string} data.username - 用户名
     * @param {string} data.bio - 个人简介
     * @param {string} [data.image] - 头像 URL
     */
    const setInfo = (data) => {
        token.value = data.token
        username.value = data.username
        bio.value = data.bio
        image.value = data.image || ''

        localStorage.setItem('token', data.token)
        localStorage.setItem('username', data.username)
        localStorage.setItem('bio', data.bio)
        localStorage.setItem('image', image.value)
    }

    /**
     * 局部更新用户信息
     *
     * 修改个人资料时调用，只更新传入的字段，防止未改字段被刷成 undefined。
     *
     * @param {Object} data - 用户信息对象（部分字段）
     * @param {string} [data.username] - 用户名
     * @param {string} [data.bio] - 个人简介
     * @param {string} [data.image] - 头像 URL
     */
    const updateInfo = (data) => {
        if (data.username !== undefined) {
            username.value = data.username
            localStorage.setItem('username', data.username)
        }
        if (data.bio !== undefined) {
            bio.value = data.bio
            localStorage.setItem('bio', data.bio)
        }
        if (data.image !== undefined) {
            image.value = data.image || ''
            localStorage.setItem('image', data.image || '')
        }
    }

    /**
     * 清除用户信息
     *
     * 退出登录时调用，清空所有状态和 localStorage。
     */
    const clearInfo = () => {
        token.value = ''
        username.value = ''
        bio.value = ''
        image.value = ''
        localStorage.clear()
    }

    return { token, username, bio, image, setInfo, updateInfo, clearInfo }
})
/**
 * 用户模块 API 接口
 *
 * 定义用户认证和个人信息相关的 API 调用，包括：
 *   - 登录/注册/退出登录
 *   - 获取用户信息
 *   - 关注/取消关注
 *   - 更新个人资料
 *
 * 所有接口均使用项目统一封装的 request 实例，自动处理 Token 注入和响应格式化。
 */

import request from '@/http/request'

/**
 * 用户登录
 *
 * @param {Object} data - 登录表单数据
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 * @returns {Promise<Object>} 响应数据，包含用户信息和 Token
 */
export function loginApi(data) {
  return request({
    url: '/api/users/login/',
    method: 'post',
    data
  })
}

/**
 * 用户注册
 *
 * @param {Object} data - 注册表单数据
 * @param {string} data.username - 用户名
 * @param {string} data.email - 邮箱
 * @param {string} data.password - 密码
 * @returns {Promise<Object>} 响应数据，包含用户信息和 Token
 */
export function registerApi(data) {
  return request({
    url: '/api/users/register/',
    method: 'post',
    data
  })
}

/**
 * 发送邮箱验证码
 *
 * @param {Object} data - { email, action: 'register'|'login'|'reset' }
 * @returns {Promise<Object>} 响应数据
 */
export function sendCodeApi(data) {
  return request({
    url: '/api/users/send_code/',
    method: 'post',
    data
  })
}

/**
 * 验证码注册
 *
 * @param {Object} data - { email, code, password, username? }
 * @returns {Promise<Object>} 响应数据，包含用户信息和 Token
 */
export function registerWithCodeApi(data) {
  return request({
    url: '/api/users/register_with_code/',
    method: 'post',
    data
  })
}

/**
 * 验证码登录
 *
 * @param {Object} data - { email, code }
 * @returns {Promise<Object>} 响应数据，包含用户信息和 Token
 */
export function loginWithCodeApi(data) {
  return request({
    url: '/api/users/login_with_code/',
    method: 'post',
    data
  })
}

/**
 * 重置密码
 *
 * @param {Object} data - { email, code, new_password }
 * @returns {Promise<Object>} 响应数据
 */
export function resetPasswordApi(data) {
  return request({
    url: '/api/users/reset_password',
    method: 'post',
    data
  })
}

/**
 * 用户退出登录
 *
 * 清除服务端 Token（加入黑名单），前端需配合清除 localStorage。
 *
 * @returns {Promise<Object>} 响应数据
 */
export function logoutApi() {
  return request({
    url: '/api/users/logout/',
    method: 'post'
  })
}

/**
 * 获取指定用户的个人信息
 *
 * @param {string} username - 目标用户的用户名
 * @returns {Promise<Object>} 响应数据，包含用户详细信息
 */
export function getProfileApi(username) {
  return request({
    url: `/api/profiles/${encodeURIComponent(username)}/`,
    method: 'get'
  })
}

/**
 * 按用户名搜索用户
 */
export function searchUsersApi(params = {}) {
  return request({
    url: '/api/profiles/',
    method: 'get',
    params
  })
}

/**
 * 获取指定用户的关注列表
 *
 * @param {string} username - 目标用户的用户名
 * @param {Object} [params] - 分页参数
 * @returns {Promise<Object>} 响应数据，包含关注用户列表
 */
export function getFollowingListApi(username, params) {
  return request({
    url: `/api/profiles/${encodeURIComponent(username)}/following/`,
    method: 'get',
    params
  })
}

/**
 * 获取指定用户的粉丝列表
 *
 * @param {string} username - 目标用户的用户名
 * @param {Object} [params] - 分页参数
 * @returns {Promise<Object>} 响应数据，包含粉丝列表
 */
export function getFollowersListApi(username, params) {
  return request({
    url: `/api/profiles/${encodeURIComponent(username)}/followers/`,
    method: 'get',
    params
  })
}

/**
 * 关注某个用户
 *
 * @param {string} username - 要关注的用户名
 * @returns {Promise<Object>} 响应数据
 */
export function followUserApi(username) {
  return request({
    url: `/api/profiles/${encodeURIComponent(username)}/follow/`,
    method: 'post'
  })
}

/**
 * 取消关注某个用户
 *
 * @param {string} username - 要取消关注的用户名
 * @returns {Promise<Object>} 响应数据
 */
export function unfollowUserApi(username) {
  return request({
    url: `/api/profiles/${encodeURIComponent(username)}/follow/`,
    method: 'delete'
  })
}

/**
 * 更新个人资料
 *
 * 支持修改简介和上传头像，使用 PATCH 方法进行局部更新。
 * 如果包含 File 对象（头像文件），Axios 会自动设置 multipart/form-data 头。
 *
 * @param {Object} data - 更新数据
 * @param {string} [data.bio] - 个人简介
 * @param {File} [data.image] - 头像文件
 * @returns {Promise<Object>} 响应数据，包含更新后的用户信息
 */
export function updateProfileApi(data) {
  return request({
    url: `/api/users/info/`,
    method: 'patch',
    data: data,
  })
}

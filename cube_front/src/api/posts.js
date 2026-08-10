/**
 * 论坛帖子模块 API 接口
 *
 * 定义帖子相关的 API 调用，包括：
 *   - 获取帖子列表/详情
 *   - 创建/更新/删除帖子
 *   - 点赞/收藏帖子
 *   - 获取我的帖子/收藏的帖子
 *   - 上传图片
 *
 * 所有接口均使用项目统一封装的 request 实例。
 */

import request from '@/http/request'

/**
 * 获取帖子列表
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @param {string} [params.category] - 分类 ID
 * @param {string} [params.keyword] - 关键词搜索
 * @returns {Promise<Object>} 响应数据，包含帖子列表和分页信息
 */
export const getPosts = (params) => {
  return request({
    url: '/api/forum/posts/',
    method: 'get',
    params
  })
}

/**
 * 获取指定用户发布的公开帖子
 */
export const getUserPosts = (username, params = {}) => getPosts({
  ...params,
  author_username: username
})

/**
 * 获取帖子详情
 *
 * @param {number} id - 帖子 ID
 * @returns {Promise<Object>} 响应数据，包含帖子详细信息和评论列表
 */
export const getPost = (id) => {
  return request({
    url: `/api/forum/posts/${id}/`,
    method: 'get'
  })
}

/**
 * 创建帖子
 *
 * 支持上传图片，使用 multipart/form-data 格式。
 *
 * @param {Object} data - 帖子数据
 * @param {string} data.title - 帖子标题
 * @param {string} data.content - 帖子内容
 * @param {number} [data.category] - 分类 ID
 * @param {File} [data.image] - 封面图片
 * @returns {Promise<Object>} 响应数据，包含创建的帖子信息
 */
export const createPost = (data) => {
  return request({
    url: '/api/forum/posts/',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 更新帖子
 *
 * @param {number} id - 帖子 ID
 * @param {Object} data - 更新数据
 * @param {string} [data.title] - 帖子标题
 * @param {string} [data.content] - 帖子内容
 * @param {number} [data.category] - 分类 ID
 * @returns {Promise<Object>} 响应数据，包含更新后的帖子信息
 */
export const updatePost = (id, data) => {
  return request({
    url: `/api/forum/posts/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除帖子
 *
 * @param {number} id - 帖子 ID
 * @returns {Promise<Object>} 响应数据
 */
export const deletePost = (id) => {
  return request({
    url: `/api/forum/posts/${id}/`,
    method: 'delete'
  })
}

/**
 * 点赞帖子
 *
 * @param {number} id - 帖子 ID
 * @returns {Promise<Object>} 响应数据，包含点赞状态
 */
export const likePost = (id) => {
  return request({
    url: `/api/forum/posts/${id}/like/`,
    method: 'post',
    data: {}
  })
}

/**
 * 收藏帖子
 *
 * @param {number} id - 帖子 ID
 * @returns {Promise<Object>} 响应数据，包含收藏状态
 */
export const collectPost = (id) => {
  return request({
    url: `/api/forum/posts/${id}/collect/`,
    method: 'post',
    data: {}
  })
}

/**
 * 获取当前用户发布的帖子
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @returns {Promise<Object>} 响应数据，包含帖子列表
 */
export const getMyPosts = (params) => {
  return request({
    url: '/api/forum/posts/my_posts/',
    method: 'get',
    params
  })
}

/**
 * 获取当前用户收藏的帖子
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @returns {Promise<Object>} 响应数据，包含收藏的帖子列表
 */
export const getCollectedPosts = (params) => {
  return request({
    url: '/api/forum/posts/collected/',
    method: 'get',
    params
  })
}

/**
 * 上传图片（帖子编辑器专用）
 *
 * @param {File} file - 图片文件
 * @returns {Promise<Object>} 响应数据，包含图片 URL
 */
export const uploadImage = (file) => {
  const formData = new FormData()
  formData.append('image', file)
  return request({
    url: '/api/forum/posts/upload_image/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取公式列表（帖子编辑器专用）
 *
 * 返回精简的公式列表，用于帖子编辑器选择公式插入。
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @param {string} [params.search] - 关键词搜索
 * @param {number} [params.category] - 分类ID
 * @param {number} [params.difficulty] - 难度等级
 * @returns {Promise<Object>} 响应数据，包含公式列表
 */
export const getFormulasForPost = (params) => {
  return request({
    url: '/api/formula/formulas/simple_list/',
    method: 'get',
    params
  })
}

/**
 * 论坛评论模块 API 接口
 *
 * 定义评论相关的 API 调用，包括：
 *   - 获取帖子评论列表
 *   - 创建评论
 *   - 删除评论
 *   - 点赞/点踩评论
 *
 * 所有接口均使用项目统一封装的 request 实例。
 */

import request from '@/http/request'

/**
 * 获取帖子的评论列表
 *
 * @param {number} postId - 帖子 ID
 * @param {Object} [data] - 查询参数
 * @param {number} [data.page] - 页码
 * @param {number} [data.page_size] - 每页数量
 * @returns {Promise<Object>} 响应数据，包含评论列表
 */
export const getComments = (postId, data) => {
  return request({
    url: `/api/forum/posts/${postId}/comments/`,
    method: 'get',
    data
  })
}

/**
 * 创建评论
 *
 * @param {Object} data - 评论数据
 * @param {number} data.post - 帖子 ID
 * @param {string} data.content - 评论内容
 * @param {number} [data.parent] - 父评论 ID（回复评论时）
 * @returns {Promise<Object>} 响应数据，包含创建的评论信息
 */
export const createComment = (data) => {
  return request({
    url: '/api/forum/comments/',
    method: 'post',
    data
  })
}

/**
 * 删除评论
 *
 * @param {number} id - 评论 ID
 * @returns {Promise<Object>} 响应数据
 */
export const deleteComment = (id) => {
  return request({
    url: `/api/forum/comments/${id}/`,
    method: 'delete'
  })
}

/**
 * 点赞评论
 *
 * @param {number} id - 评论 ID
 * @returns {Promise<Object>} 响应数据，包含点赞状态
 */
export const likeComment = (id) => {
  return request({
    url: `/api/forum/comments/${id}/like/`,
    method: 'post',
    data: {}
  })
}

/**
 * 点踩评论
 *
 * @param {number} id - 评论 ID
 * @returns {Promise<Object>} 响应数据，包含点踩状态
 */
export const dislikeComment = (id) => {
  return request({
    url: `/api/forum/comments/${id}/dislike/`,
    method: 'post',
    data: {}
  })
}
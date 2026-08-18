/**
 * 论坛模块 API 接口
 *
 * 包含帖子 CRUD、点赞/收藏、评论、标签等接口。
 */

import request from '@/http/request'

// ─── 帖子接口 ──────────────────────────────────────

/** 帖子列表 */
export function getPosts(params = {}) {
  return request({ url: '/api/forum/posts/', method: 'get', params })
}

/** 热门帖子 */
export function getHotPosts(params = {}) {
  return request({ url: '/api/forum/posts/hot/', method: 'get', params })
}

/** 帖子详情 */
export function getPost(id) {
  return request({ url: `/api/forum/posts/${id}/`, method: 'get' })
}

/** 点赞/取消点赞 */
export function likePost(id) {
  return request({ url: `/api/forum/posts/${id}/like/`, method: 'post' })
}

/** 收藏/取消收藏 */
export function collectPost(id) {
  return request({ url: `/api/forum/posts/${id}/collect/`, method: 'post' })
}

/** 我的帖子 */
export function getMyPosts(params = {}) {
  return request({ url: '/api/forum/posts/my_posts/', method: 'get', params })
}

/** 我的收藏 */
export function getCollectedPosts(params = {}) {
  return request({ url: '/api/forum/posts/collected/', method: 'get', params })
}

/** 创建帖子（FormData） */
export function createPost(data) {
  return request({ url: '/api/forum/posts/', method: 'post', data })
}

/** 更新帖子（FormData） */
export function updatePost(id, data) {
  return request({ url: `/api/forum/posts/${id}/`, method: 'put', data })
}

/** 删除帖子 */
export function deletePost(id) {
  return request({ url: `/api/forum/posts/${id}/`, method: 'delete' })
}

/** 上传帖子图片 */
export function uploadPostImage(file) {
  const formData = new FormData()
  formData.append('image', file)
  return request({ url: '/api/forum/posts/upload_image/', method: 'post', data: formData })
}

/** 获取标签列表 */
export function getTags(params = {}) {
  return request({ url: '/api/forum/tags/', method: 'get', params })
}

// ─── 评论接口 ──────────────────────────────────────

/** 帖子评论列表 */
export function getComments(postId, params = {}) {
  return request({ url: `/api/forum/posts/${postId}/comments/`, method: 'get', params })
}

/** 发表评论 */
export function createComment(data) {
  return request({ url: '/api/forum/comments/', method: 'post', data })
}

/** 删除评论 */
export function deleteComment(id) {
  return request({ url: `/api/forum/comments/${id}/`, method: 'delete' })
}

/** 点赞评论 */
export function likeComment(id) {
  return request({ url: `/api/forum/comments/${id}/like/`, method: 'post' })
}

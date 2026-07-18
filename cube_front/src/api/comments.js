// src/api/comments.js
import request from '@/http/request'

// 获取帖子评论
export const getComments = (postId, data) => {
  return request({
    url: `/api/forum/posts/${postId}/comments/`,
    method: 'get',
    data
  })
}

// 创建评论
export const createComment = (data) => {
  return request({
    url: '/api/forum/comments/',
    method: 'post',
    data
  })
}

// 删除评论
export const deleteComment = (id) => {
  return request({
    url: `/api/forum/comments/${id}/`,
    method: 'delete'
  })
}

// 点赞评论
export const likeComment = (id) => {
  return request({
    url: `/api/forum/comments/${id}/like/`,
    method: 'post',
    data: {}
  })
}

// 点踩评论
export const dislikeComment = (id) => {
  return request({
    url: `/api/forum/comments/${id}/dislike/`,
    method: 'post',
    data: {}
  })
}
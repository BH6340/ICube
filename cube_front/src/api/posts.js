// src/api/posts.js
import request from '@/http/request'

// 获取帖子列表
export const getPosts = (params) => {
  return request({
    url: '/api/forum/posts/',
    method: 'get',
    params
  })
}

// 获取帖子详情
export const getPost = (id) => {
  return request({
    url: `/api/forum/posts/${id}/`,
    method: 'get'
  })
}

// 创建帖子
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

// 更新帖子
export const updatePost = (id, data) => {
  return request({
    url: `/api/forum/posts/${id}/`,
    method: 'put',
    data
  })
}

// 删除帖子
export const deletePost = (id) => {
  return request({
    url: `/api/forum/posts/${id}/`,
    method: 'delete'
  })
}

// 点赞帖子
export const likePost = (id) => {
  return request({
    url: `/api/forum/posts/${id}/like/`,
    method: 'post',
    data: {}
  })
}

// 收藏帖子
export const collectPost = (id) => {
  return request({
    url: `/api/forum/posts/${id}/collect/`,
    method: 'post',
    data: {}
  })
}

// 获取我的帖子
export const getMyPosts = (params) => {
  return request({
    url: '/api/forum/posts/my_posts/',
    method: 'get',
    params
  })
}

// 获取我收藏的帖子
export const getCollectedPosts = (params) => {
  return request({
    url: '/api/forum/posts/collected/',
    method: 'get',
    params
  })
}

// 上传图片
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
// src/api/tags.js
import request from '@/http/request'

export const getTags = (params) => {
  return request({
    url: '/api/forum/tags/',
    method: 'get',
    params
  })
}
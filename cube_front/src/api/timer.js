import request from '@/http/request'

export function createTimerRecord(data) {
  return request({
    url: '/api/timer/records/',
    method: 'post',
    data
  })
}

export function getTimerRecords(params) {
  return request({
    url: '/api/timer/records/',
    method: 'get',
    params
  })
}

export function deleteTimerRecord(id) {
  return request({
    url: `/api/timer/records/${id}/`,
    method: 'delete'
  })
}

export function getTimerStats(params) {
  return request({
    url: '/api/timer/records/stats/',
    method: 'get',
    params
  })
}

export function getTimerTrend(params) {
  return request({
    url: '/api/timer/records/trend/',
    method: 'get',
    params
  })
}
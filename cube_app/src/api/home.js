import request from '@/http/request'

/** 获取最新 APP 版本信息 */
export function getLatestVersion() {
  return request({
    url: '/api/home/app/version/',
    method: 'get'
  })
}

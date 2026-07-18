// src/api/user.js (或 src/api/home.js)
import request from '@/http/request' // 确保引入了你项目封装的 Axios 实例

/**
 * 从后端动态获取导航栏菜单数据
 * @returns {Promise} 返回统一封装的响应体 { code: 100, msg: "...", data: [...] }
 */
export function getMenusApi() {
  return request({
    url: '/api/home/navigation/menus/',
    method: 'get'
  })
}
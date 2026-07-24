/**
 * 首页导航模块 API 接口
 *
 * 定义首页导航菜单相关的 API 调用，主要用于动态获取导航栏配置。
 */

import request from '@/http/request'

/**
 * 从后端动态获取导航栏菜单数据
 *
 * 获取主导航栏和个人中心导航栏的菜单配置，用于前端动态渲染。
 *
 * @returns {Promise<Object>} 返回统一封装的响应体 { code: 100, msg: "...", data: [...] }
 */
export function getMenusApi() {
  return request({
    url: '/api/home/navigation/menus/',
    method: 'get'
  })
}

/**
 * 从后端动态获取轮播图数据
 *
 * 获取首页轮播图列表，包含标题、描述、图片、链接等信息，用于前端动态渲染轮播图。
 *
 * @returns {Promise<Object>} 返回统一封装的响应体 { code: 100, msg: "...", data: [...] }
 */
export function getBannersApi() {
  return request({
    url: '/api/home/banners/',
    method: 'get'
  })
}
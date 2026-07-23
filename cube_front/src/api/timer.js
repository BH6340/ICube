/**
 * 计时器模块 API 接口
 *
 * 定义计时记录相关的 API 调用，包括：
 *   - 创建/查询/删除计时记录
 *   - 获取分组统计（按魔方类型和还原方法）
 *   - 获取趋势统计（按日期分组）
 *
 * 所有接口均使用项目统一封装的 request 实例。
 */

import request from '@/http/request'

/**
 * 创建计时记录
 *
 * @param {Object} data - 计时记录数据
 * @param {string} [data.cube_type] - 魔方类型（默认 3x3）
 * @param {string} [data.method] - 还原方法（默认 layer）
 * @param {number} data.time_ms - 还原时间（毫秒）
 * @param {string} [data.scramble] - 打乱公式
 * @returns {Promise<Object>} 响应数据，包含创建的记录信息
 */
export function createTimerRecord(data) {
  return request({
    url: '/api/timer/records/',
    method: 'post',
    data
  })
}

/**
 * 获取计时记录列表
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @param {string} [params.cube_type] - 魔方类型过滤
 * @param {string} [params.method] - 还原方法过滤
 * @param {string} [params.start_date] - 开始日期（格式 YYYY-MM-DD）
 * @param {string} [params.end_date] - 结束日期（格式 YYYY-MM-DD）
 * @returns {Promise<Object>} 响应数据，包含记录列表和分页信息
 */
export function getTimerRecords(params) {
  return request({
    url: '/api/timer/records/',
    method: 'get',
    params
  })
}

/**
 * 删除计时记录
 *
 * @param {number} id - 计时记录 ID
 * @returns {Promise<Object>} 响应数据
 */
export function deleteTimerRecord(id) {
  return request({
    url: `/api/timer/records/${id}/`,
    method: 'delete'
  })
}

/**
 * 获取分组统计信息
 *
 * 按魔方类型和还原方法分组，计算每组的最佳成绩、平均成绩和记录数。
 *
 * @param {Object} [params] - 查询参数
 * @param {string} [params.cube_type] - 魔方类型过滤
 * @param {string} [params.method] - 还原方法过滤
 * @returns {Promise<Object>} 响应数据，包含分组统计和总体统计
 */
export function getTimerStats(params) {
  return request({
    url: '/api/timer/records/stats/',
    method: 'get',
    params
  })
}

/**
 * 获取趋势统计信息
 *
 * 按日期分组，计算每天的最佳成绩和平均成绩。
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.days] - 统计天数（默认 30 天）
 * @param {string} [params.cube_type] - 魔方类型过滤
 * @param {string} [params.method] - 还原方法过滤
 * @returns {Promise<Object>} 响应数据，包含按日期分组的统计列表
 */
export function getTimerTrend(params) {
  return request({
    url: '/api/timer/records/trend/',
    method: 'get',
    params
  })
}
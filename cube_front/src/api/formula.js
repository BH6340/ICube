/**
 * 公式库模块 API 接口
 *
 * 定义魔方公式相关的 API 调用，包括：
 *   - 获取公式分类
 *   - 获取公式列表/详情
 *   - 创建/更新/删除公式
 *   - 公式匹配（根据当前状态匹配适用公式）
 *   - 公式收藏管理
 *
 * 所有接口均使用项目统一封装的 request 实例。
 */

import request from '@/http/request'

/**
 * 获取公式分类列表
 *
 * @returns {Promise<Object>} 响应数据，包含分类列表（系统分类 + 当前用户的自定义分类）
 */
export const getFormulaCategories = () => {
  return request({
    url: '/api/formula/categories/',
    method: 'get'
  })
}

// === 分类管理 ===

/**
 * 获取当前用户的自定义分类
 *
 * @returns {Promise<Object>} 响应数据，包含当前用户的自定义分类列表
 */
export const getMyCustomCategories = () => {
  return request({
    url: '/api/formula/categories/my_custom/',
    method: 'get'
  })
}

/**
 * 创建自定义分类
 *
 * @param {Object} data - 分类数据
 * @param {string} data.name - 分类名称
 * @param {number} data.order - 阶数（3/4/5）
 * @param {string} data.method - 求解方法
 * @param {string} data.phase - 阶段
 * @returns {Promise<Object>} 响应数据，包含创建的分类信息
 */
export const createCategory = (data) => {
  return request({
    url: '/api/formula/categories/',
    method: 'post',
    data
  })
}

/**
 * 删除自定义分类
 *
 * @param {number} id - 分类 ID
 * @returns {Promise<Object>} 响应数据
 */
export const deleteCategory = (id) => {
  return request({
    url: `/api/formula/categories/${id}/`,
    method: 'delete'
  })
}

/**
 * 阶段选项（固定列表，用于创建分类时选择）
 *
 * 包含魔方各求解方法的常见阶段
 */
export const PHASE_OPTIONS = [
  'Cross', 'F2L', 'OLL', 'PLL', 'Full PLL',
  'Edge Control', 'EOLine', 'EOCross', 'F2L+OLL',
  'Block Building', 'Layer-by-Layer', '其他'
]

/**
 * 求解方法选项
 *
 * 包含主流的魔方求解方法
 */
export const METHOD_OPTIONS = ['层先法', 'CFOP', '桥式法', 'ZZ法', 'Heise法', '自创']

/**
 * 获取公式作者列表
 *
 * @returns {Promise<Object>} 响应数据，包含作者列表（id 和 username）
 */
export const getFormulaAuthors = () => {
  return request({
    url: '/api/formula/formulas/authors/',
    method: 'get'
  })
}

/**
 * 获取公式列表
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @param {number} [params.category] - 分类 ID
 * @param {string} [params.difficulty] - 难度等级（支持多值）
 * @param {string} [params.created_by] - 作者 ID（支持多值）
 * @param {boolean} [params.is_custom] - 是否自定义公式
 * @param {string} [params.search] - 关键词搜索
 * @returns {Promise<Object>} 响应数据，包含公式列表和分页信息
 */
export const getFormulaList = (params = {}) => {
  return request({
    url: '/api/formula/formulas/',
    method: 'get',
    params
  })
}

/**
 * 获取指定用户创建的公开自定义公式
 */
export const getUserCustomFormulas = (username, params = {}) =>
  getFormulaList({
    ...params,
    author_username: username,
    is_custom: true
  })

/**
 * 获取指定用户公开收藏的公式
 */
export const getUserFormulaCollections = (username, params = {}) => {
  return request({
    url: `/api/formula/collections/users/${encodeURIComponent(username)}/`,
    method: 'get',
    params
  })
}

/**
 * 获取公式详情
 *
 * @param {number} id - 公式 ID
 * @returns {Promise<Object>} 响应数据，包含公式详细信息
 */
export const getFormulaDetail = (id) => {
  return request({
    url: `/api/formula/formulas/${id}/`,
    method: 'get'
  })
}

/**
 * 创建自定义公式
 *
 * @param {Object} data - 公式数据
 * @param {string} data.name - 公式名称
 * @param {string} data.notation - 公式记号
 * @param {number} [data.category] - 分类 ID
 * @param {string} [data.difficulty] - 难度等级
 * @param {string} [data.description] - 公式描述
 * @returns {Promise<Object>} 响应数据，包含创建的公式信息
 */
export const createFormula = (data) => {
  return request({
    url: '/api/formula/formulas/',
    method: 'post',
    data
  })
}

/**
 * 更新公式
 *
 * @param {number} id - 公式 ID
 * @param {Object} data - 更新数据
 * @returns {Promise<Object>} 响应数据，包含更新后的公式信息
 */
export const updateFormula = (id, data) => {
  return request({
    url: `/api/formula/formulas/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除公式
 *
 * @param {number} id - 公式 ID
 * @returns {Promise<Object>} 响应数据
 */
export const deleteFormula = (id) => {
  return request({
    url: `/api/formula/formulas/${id}/`,
    method: 'delete'
  })
}

/**
 * 根据当前状态匹配适用公式
 *
 * 用户提交当前魔方状态，系统返回匹配的公式列表。
 *
 * @param {Object} data - 状态数据
 * @param {Object} data.state - 当前魔方状态定义
 * @returns {Promise<Object>} 响应数据，包含匹配的公式列表
 */
export const matchFormula = (data) => {
  return request({
    url: '/api/formula/formulas/match/',
    method: 'post',
    data
  })
}

/**
 * 获取我的公式收藏列表
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @returns {Promise<Object>} 响应数据，包含收藏列表
 */
export const getMyCollections = (params = {}) => {
  return request({
    url: '/api/formula/collections/',
    method: 'get',
    params
  })
}

/**
 * 获取我创建的自定义公式列表
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @returns {Promise<Object>} 响应数据，包含公式列表
 */
export const getMyCustomFormulas = (params = {}) => {
  return request({
    url: '/api/formula/formulas/my_custom/',
    method: 'get',
    params
  })
}

/**
 * 添加公式收藏
 *
 * @param {number} formulaId - 公式 ID
 * @returns {Promise<Object>} 响应数据，包含收藏信息
 */
export const addCollection = (formulaId) => {
  return request({
    url: '/api/formula/collections/',
    method: 'post',
    data: { formula: formulaId }
  })
}

/**
 * 移除公式收藏
 *
 * @param {number} collectionId - 收藏记录 ID
 * @returns {Promise<Object>} 响应数据
 */
export const removeCollection = (collectionId) => {
  return request({
    url: `/api/formula/collections/${collectionId}/`,
    method: 'delete'
  })
}

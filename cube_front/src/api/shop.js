/**
 * 商城模块 API 接口
 *
 * 定义商城相关的 API 调用，包括：
 *   - 获取商品分类/列表/详情
 *   - 购物车增删改查
 *   - 订单创建/查询/详情
 *   - 订单支付/取消/确认收货
 *
 * 所有接口均使用项目统一封装的 request 实例。
 */

import request from '@/http/request'

/**
 * 获取商品分类列表
 *
 * @returns {Promise<Object>} 响应数据，包含分类树形结构
 */
export const getCategories = () => {
  return request({
    url: '/api/shop/categories/',
    method: 'get'
  })
}

/**
 * 获取商品列表
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @param {number} [params.category] - 分类 ID（包含子分类）
 * @param {number} [params.price_min] - 最低价格
 * @param {number} [params.price_max] - 最高价格
 * @param {string} [params.keyword] - 关键词搜索
 * @param {string} [params.sort] - 排序字段（默认 -created_at）
 * @returns {Promise<Object>} 响应数据，包含商品列表和分页信息
 */
export const getProducts = (params = {}) => {
  return request({
    url: '/api/shop/products/',
    method: 'get',
    params
  })
}

/**
 * 获取商品详情
 *
 * @param {number} id - 商品 ID
 * @returns {Promise<Object>} 响应数据，包含商品详细信息
 */
export const getProductDetail = (id) => {
  return request({
    url: `/api/shop/products/${id}/`,
    method: 'get'
  })
}

/**
 * 获取当前用户的购物车
 *
 * @returns {Promise<Object>} 响应数据，包含购物车列表
 */
export const getCart = () => {
  return request({
    url: '/api/shop/cart/',
    method: 'get'
  })
}

/**
 * 添加商品到购物车
 *
 * 如果购物车已存在相同商品且规格相同，数量累加。
 *
 * @param {Object} data - 购物车数据
 * @param {number} data.product - 商品 ID
 * @param {number} [data.quantity] - 数量（默认 1）
 * @param {Object} [data.selected_spec] - 选中规格
 * @returns {Promise<Object>} 响应数据，包含购物车记录
 */
export const addToCart = (data) => {
  return request({
    url: '/api/shop/cart/',
    method: 'post',
    data
  })
}

/**
 * 更新购物车数量
 *
 * 如果数量 <= 0，自动删除购物车记录。
 *
 * @param {number} id - 购物车记录 ID
 * @param {Object} data - 更新数据
 * @param {number} data.quantity - 数量
 * @returns {Promise<Object>} 响应数据，包含更新后的购物车记录
 */
export const updateCart = (id, data) => {
  return request({
    url: `/api/shop/cart/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除购物车记录
 *
 * @param {number} id - 购物车记录 ID
 * @returns {Promise<Object>} 响应数据
 */
export const deleteCartItem = (id) => {
  return request({
    url: `/api/shop/cart/${id}/`,
    method: 'delete'
  })
}

/**
 * 创建订单
 *
 * 从购物车选择商品创建订单，自动扣减库存。
 *
 * @param {Object} data - 订单数据
 * @param {number[]} data.cart_ids - 购物车记录 ID 列表
 * @param {Object} data.address - 收货地址
 * @returns {Promise<Object>} 响应数据，包含创建的订单信息
 */
export const createOrder = (data) => {
  return request({
    url: '/api/shop/orders/',
    method: 'post',
    data
  })
}

/**
 * 获取当前用户的订单列表
 *
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @param {string} [params.status] - 订单状态过滤
 * @returns {Promise<Object>} 响应数据，包含订单列表
 */
export const getOrders = (params = {}) => {
  return request({
    url: '/api/shop/orders/',
    method: 'get',
    params
  })
}

/**
 * 获取订单详情
 *
 * @param {number|string} id - 订单 ID 或订单号
 * @returns {Promise<Object>} 响应数据，包含订单详细信息
 */
export const getOrderDetail = (id) => {
  return request({
    url: `/api/shop/orders/${id}/`,
    method: 'get'
  })
}

/**
 * 获取订单支付链接
 *
 * @param {number} id - 订单 ID
 * @returns {Promise<Object>} 响应数据，包含支付 URL
 */
export const payOrder = (id) => {
  return request({
    url: `/api/shop/orders/${id}/pay/`,
    method: 'put'
  })
}

/**
 * 取消订单
 *
 * 仅待付款和已付款状态的订单可取消，取消后库存回滚。
 *
 * @param {number} id - 订单 ID
 * @returns {Promise<Object>} 响应数据，包含取消后的订单信息
 */
export const cancelOrder = (id) => {
  return request({
    url: `/api/shop/orders/${id}/cancel/`,
    method: 'put'
  })
}

/**
 * 确认收货
 *
 * 仅已发货状态的订单可确认收货。
 *
 * @param {number} id - 订单 ID
 * @returns {Promise<Object>} 响应数据，包含确认后的订单信息
 */
export const completeOrder = (id) => {
  return request({
    url: `/api/shop/orders/${id}/complete/`,
    method: 'put'
  })
}

/**
 * 获取当前用户的收货地址列表
 *
 * @returns {Promise<Object>} 响应数据，包含地址列表
 */
export const getAddresses = () => {
  return request({
    url: '/api/shop/addresses/',
    method: 'get'
  })
}

/**
 * 创建收货地址
 *
 * @param {Object} data - 地址数据
 * @param {string} data.name - 收货人姓名
 * @param {string} data.phone - 联系电话
 * @param {string} data.province - 省份
 * @param {string} data.city - 城市
 * @param {string} data.district - 区县
 * @param {string} data.detail - 详细地址
 * @param {boolean} [data.is_default] - 是否设为默认地址
 * @param {number} [data.sort_order] - 排序
 * @returns {Promise<Object>} 响应数据，包含创建的地址信息
 */
export const createAddress = (data) => {
  return request({
    url: '/api/shop/addresses/',
    method: 'post',
    data
  })
}

/**
 * 更新收货地址
 *
 * @param {number} id - 地址 ID
 * @param {Object} data - 更新数据
 * @param {string} [data.name] - 收货人姓名
 * @param {string} [data.phone] - 联系电话
 * @param {string} [data.province] - 省份
 * @param {string} [data.city] - 城市
 * @param {string} [data.district] - 区县
 * @param {string} [data.detail] - 详细地址
 * @param {boolean} [data.is_default] - 是否设为默认地址
 * @param {number} [data.sort_order] - 排序
 * @returns {Promise<Object>} 响应数据，包含更新后的地址信息
 */
export const updateAddress = (id, data) => {
  return request({
    url: `/api/shop/addresses/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除收货地址
 *
 * @param {number} id - 地址 ID
 * @returns {Promise<Object>} 响应数据
 */
export const deleteAddress = (id) => {
  return request({
    url: `/api/shop/addresses/${id}/`,
    method: 'delete'
  })
}

/**
 * 设置默认地址
 *
 * @param {number} id - 地址 ID
 * @returns {Promise<Object>} 响应数据，包含更新后的地址信息
 */
export const setDefaultAddress = (id) => {
  return request({
    url: `/api/shop/addresses/${id}/set_default/`,
    method: 'post'
  })
}
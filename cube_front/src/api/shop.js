import request from '@/http/request'

export const getCategories = () => {
  return request({
    url: '/api/shop/categories/',
    method: 'get'
  })
}

export const getProducts = (params = {}) => {
  return request({
    url: '/api/shop/products/',
    method: 'get',
    params
  })
}

export const getProductDetail = (id) => {
  return request({
    url: `/api/shop/products/${id}/`,
    method: 'get'
  })
}

export const getCart = () => {
  return request({
    url: '/api/shop/cart/',
    method: 'get'
  })
}

export const addToCart = (data) => {
  return request({
    url: '/api/shop/cart/',
    method: 'post',
    data
  })
}

export const updateCart = (id, data) => {
  return request({
    url: `/api/shop/cart/${id}/`,
    method: 'put',
    data
  })
}

export const deleteCartItem = (id) => {
  return request({
    url: `/api/shop/cart/${id}/`,
    method: 'delete'
  })
}

export const createOrder = (data) => {
  return request({
    url: '/api/shop/orders/',
    method: 'post',
    data
  })
}

export const getOrders = (params = {}) => {
  return request({
    url: '/api/shop/orders/',
    method: 'get',
    params
  })
}

export const getOrderDetail = (id) => {
  return request({
    url: `/api/shop/orders/${id}/`,
    method: 'get'
  })
}

export const payOrder = (id) => {
  return request({
    url: `/api/shop/orders/${id}/pay/`,
    method: 'put'
  })
}

export const cancelOrder = (id) => {
  return request({
    url: `/api/shop/orders/${id}/cancel/`,
    method: 'put'
  })
}

export const completeOrder = (id) => {
  return request({
    url: `/api/shop/orders/${id}/complete/`,
    method: 'put'
  })
}
import request from '../http/request'

export const getFormulaCategories = () => {
  return request({
    url: '/api/formula/categories/',
    method: 'get'
  })
}

export const getFormulaList = (params = {}) => {
  return request({
    url: '/api/formula/formulas/',
    method: 'get',
    params
  })
}

export const getFormulaDetail = (id) => {
  return request({
    url: `/api/formula/formulas/${id}/`,
    method: 'get'
  })
}

export const createFormula = (data) => {
  return request({
    url: '/api/formula/formulas/',
    method: 'post',
    data
  })
}

export const updateFormula = (id, data) => {
  return request({
    url: `/api/formula/formulas/${id}/`,
    method: 'put',
    data
  })
}

export const deleteFormula = (id) => {
  return request({
    url: `/api/formula/formulas/${id}/`,
    method: 'delete'
  })
}

export const matchFormula = (data) => {
  return request({
    url: '/api/formula/formulas/match/',
    method: 'post',
    data
  })
}

export const getMyCollections = (params = {}) => {
  return request({
    url: '/api/formula/collections/',
    method: 'get',
    params
  })
}

export const addCollection = (formulaId) => {
  return request({
    url: '/api/formula/collections/',
    method: 'post',
    data: { formula: formulaId }
  })
}

export const removeCollection = (collectionId) => {
  return request({
    url: `/api/formula/collections/${collectionId}/`,
    method: 'delete'
  })
}
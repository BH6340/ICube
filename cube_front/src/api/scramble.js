import request from '@/http/request'

/**
 * 生成单个打乱公式
 * @param {string} cubeType - 魔方类型：2x2/3x3/4x4/5x5
 * @returns {Promise<{scramble: string, scramble_id: string, cube_type: string, from_cache: boolean}>}
 */
export function generateScramble(cubeType = '3x3') {
  return request.get('/api/scramble/generate', {
    params: { cube_type: cubeType }
  })
}

/**
 * 批量生成打乱公式
 * @param {string} cubeType - 魔方类型
 * @param {number} count - 数量，最大 100
 */
export function generateScrambleBatch(cubeType, count = 10) {
  return request.get('/api/scramble/batch', {
    params: { cube_type: cubeType, count }
  })
}

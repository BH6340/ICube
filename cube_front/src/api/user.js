import request from '@/http/request'


// 登录
export function loginApi(data) {
  return request({
    url: '/api/users/login', // 替换为你真实的 URL
    method: 'post',
    data
  })
}

// 注册
export function registerApi(data) {
  return request({
    url: '/api/users/register',
    method: 'post',
    data
  })
}

// 退出登录
export function logoutApi() {
  return request({
    url: '/api/users/logout',
    method: 'post'
  })
}

// 获取用户信息
export function getProfileApi(username) {
  return request({
    url: `/api/profiles/${username}`, // 根据后端实际路由前缀微调，比如 /api/profiles/
    method: 'get'
  })
}

/**
 * 获取指定用户的关注列表
 * @param {string} username - 目标用户的用户名
 */
export function getFollowingListApi(username) {
  return request({
    url: `/api/profiles/${username}/following`,
    method: 'get'
  })
}

/**
 * 获取指定用户的粉丝列表
 * @param {string} username - 目标用户的用户名
 */
export function getFollowersListApi(username) {
  return request({
    url: `/api/profiles/${username}/followers`,
    method: 'get'
  })
}

// 4. 关注某个用户
export function followUserApi(username) {
  return request({
    url: `/api/profiles/${username}/follow`, // 或者是你后端定义的实际关注 URL
    method: 'post'
  })
}

// 5. 取消关注某个用户
export function unfollowUserApi(username) {
  return request({
    url: `/api/profiles/${username}/follow`, // 或者是通过 delete 方法：method: 'delete'
    method: 'delete'
  })
}

// 6. 更新个人资料 (支持修改简介和上传头像)
export function updateProfileApi(data) {
  return request({
    url: `/api/users/info`, // 对齐你的 Django 个人资料路由
    method: 'patch', // 使用 patch 进行局部更新
    data: data,
    // 如果你要传原生 File 对象(头像文件)，Axios 会自动帮你把 headers 设为 multipart/form-data
  })
}
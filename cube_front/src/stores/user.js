import {defineStore} from 'pinia'
import {ref} from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const bio = ref(localStorage.getItem('bio') || '')
  const image = ref(localStorage.getItem('image') || '')

  const setInfo = (data) => {
    // 直接传入整个 user 对象更方便
    token.value = data.token
    username.value = data.username
    bio.value = data.bio
    image.value = data.image || ''

    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('bio', data.bio)
    localStorage.setItem('image', image.value)
  }

  // 💡 核心新增：专门用于修改个人资料时的“局部同步方法”
  const updateInfo = (data) => {
    // 只有当后端返回了对应字段时才更新，防止未改字段被刷成 undefined
    if (data.username !== undefined) {
      username.value = data.username
      localStorage.setItem('username', data.username)
    }
    if (data.bio !== undefined) {
      bio.value = data.bio
      localStorage.setItem('bio', data.bio)
    }
    if (data.image !== undefined) {
      image.value = data.image || ''
      localStorage.setItem('image', data.image || '')
    }
  }

  const clearInfo = () => {
    token.value = ''
    username.value = ''
    bio.value = ''
    image.value = ''
    localStorage.clear() // 或者逐个 remove
  }

  return { token, username, bio, image, setInfo, updateInfo, clearInfo }
})
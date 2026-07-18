<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <h2>登录 ICube</h2>
      <el-form :model="loginForm" :rules="rules" ref="loginRef" label-position="top">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="loginForm.email" placeholder="example@mail.com"/>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码"/>
        </el-form-item>

        <el-button type="primary" class="full-width" @click="handleLogin(loginRef)">登录</el-button>

        <div class="auth-footer">
          <span>新用户？</span>
          <el-link type="primary" style="font-size: 14px; vertical-align: baseline;" @click="$router.push('/register')">
            创建账号
          </el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import {ref, reactive} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {loginApi} from '@/api/user'
import {useUserStore} from '@/stores/user'


const router = useRouter()
const loginRef = ref()
const loginForm = reactive({email: '', password: ''})
const userStore = useUserStore()

const rules = {
  email: [{required: true, message: '请输入邮箱', trigger: 'blur'}],
  password: [{required: true, message: '请输入密码', trigger: 'blur'}]
}

const handleLogin = async (formEl) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      try {
        const postData = {
          user: {
            email: loginForm.email,
            password: loginForm.password
          }
        }
        const res = await loginApi(postData)
        // res 是整个对象，res.user 是内层对象
        if (res.code === 100) {
          const userData = res.user

          // 将 token 和 username 传给 Pinia
          userStore.setInfo(res.user)

          ElMessage.success('登录成功，欢迎 ' + userData.username)
          await router.push('/')
        } else {
          // 处理 code 不为 100 的业务错误
          ElMessage.error(res.msg || '登录失败')
        }
      } catch (err) {
        console.error('登录失败', err)
      }
    }
  })
}
</script>

<style scoped>
/* 样式与注册页一致 */
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
}

.auth-card {
  width: 400px;
  padding: 20px;
}

.full-width {
  width: 100%;
  margin-top: 20px;
}

.auth-footer {
  margin-top: 15px;
  text-align: center;
  font-size: 14px;
}

h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #409EFF;
}
</style>
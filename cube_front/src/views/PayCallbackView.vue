<template>
  <div class="callback-view">
    <el-icon size="48" color="#409EFF"><Loading /></el-icon>
    <p>处理支付结果...</p>
  </div>
</template>

<script setup>
/**
 * PayCallbackView.vue - 支付回调处理页面
 *
 * 核心职责：
 * 1. 接收第三方支付回调参数
 * 2. 解析订单号并重定向到支付结果页
 *
 * 设计要点：
 * - 作为支付网关的回调接收点，仅做参数转发
 * - 根据 out_trade_no 或 orderNo 跳转到支付详情页
 * - 无订单号则跳转到订单列表
 */
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

onMounted(() => {
  const orderNo = route.query.out_trade_no || route.query.orderNo
  if (orderNo) {
    router.replace(`/shop/pay/${orderNo}`)
  } else {
    router.replace('/profiles/orders')
  }
})
</script>

<style scoped>
.callback-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  gap: 20px;
  color: #909399;
  font-size: 16px;
}
</style>

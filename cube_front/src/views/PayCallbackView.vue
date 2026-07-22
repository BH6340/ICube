<template>
  <div class="callback-view">
    <el-icon size="48" color="#409EFF"><Loading /></el-icon>
    <p>处理支付结果...</p>
  </div>
</template>

<script setup>
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

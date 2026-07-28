<template>
  <div class="pay-view">
    <el-card shadow="never" class="pay-card">
      <template #header>
        <span>订单支付</span>
      </template>

      <div v-if="!order" class="loading">
        <el-icon size="48" color="#409EFF"><Loading /></el-icon>
      </div>

      <div v-else class="pay-content">
        <div class="order-info">
          <div class="info-row">
            <span class="label">订单号:</span>
            <span class="value">{{ order.order_no }}</span>
          </div>
          <div class="info-row">
            <span class="label">订单金额:</span>
            <span class="value amount">¥{{ order.total_amount }}</span>
          </div>
          <div class="info-row">
            <span class="label">订单状态:</span>
            <span class="value status">{{ getStatusText(order.status) }}</span>
          </div>
        </div>

        <el-divider />

        <!-- 已支付 -->
        <div v-if="order.status === 'paid'" class="paid-success">
          <el-icon size="48" color="#67c23a"><CircleCheck /></el-icon>
          <h3>支付成功</h3>
          <p>您的订单已成功支付</p>
          <el-button type="primary" @click="goToOrders">查看订单</el-button>
        </div>

        <!-- 已取消 -->
        <div v-else-if="order.status === 'cancelled'" class="cancelled">
          <el-icon size="48" color="#f56c6c"><CircleClose /></el-icon>
          <h3>订单已取消</h3>
          <el-button type="primary" @click="goToOrders">查看订单</el-button>
        </div>

        <!-- 待支付 -->
        <div v-else class="pay-methods">
          <h4>选择支付方式</h4>
          <div class="method-item">
            <el-radio v-model="selectedMethod" value="alipay">
              <div class="method-icon">
                <el-icon size="24" color="#1677ff"><CreditCard /></el-icon>
              </div>
              <span>支付宝支付</span>
            </el-radio>
          </div>

          <div v-if="payUrl" class="payment-section">
            <div class="pay-redirect">
              <p class="redirect-tip">点击下方按钮跳转到支付宝支付</p>
              <el-button type="primary" size="large" @click="goToPayPage">
                前往支付宝支付
              </el-button>
            </div>
            <p class="polling-hint">
              <el-icon><Loading /></el-icon>
              等待支付结果...
              <el-button size="small" text type="primary" @click="checkOrderStatus">手动刷新状态</el-button>
            </p>
          </div>

          <div v-else class="no-alipay">
            <el-alert title="支付接口异常" description="支付宝支付接口暂时不可用，请稍后重试" type="error" show-icon />
          </div>

          <div class="pay-actions">
            <el-button type="primary" size="large" :loading="payLoading" @click="handlePay" :disabled="!!payUrl">
              {{ payLoading ? '支付中...' : '立即支付' }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
/**
 * PayView.vue - 支付页面
 *
 * 核心职责：
 * 1. 展示订单详情和支付金额
 * 2. 提供多种支付方式选择（支付宝/微信）
 * 3. 发起支付并轮询检查支付结果
 *
 * 功能特性：
 *   - 支付方式 Tab 切换
 *   - 生成支付二维码/链接
 *   - 轮询机制检测支付状态变化
 *   - 支付成功后跳转订单详情
 *
 * 设计要点：
 *   - pollingTimer 用于支付状态轮询（3秒间隔）
 *   - 组件卸载时清理定时器，避免内存泄漏
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, CircleClose, CreditCard, Loading } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { getOrderDetail, payOrder } from '@/api/shop'

const route = useRoute()
const router = useRouter()
const order = ref(null)
const payUrl = ref(null)
const payLoading = ref(false)
const selectedMethod = ref('alipay')
const pollingTimer = ref(null)

const getStatusText = (status) => {
  const statusMap = { pending: '待付款', paid: '已付款', shipped: '已发货', completed: '已完成', cancelled: '已取消' }
  return statusMap[status] || status
}

const goToOrders = () => router.push('/profiles/orders')

const goToPayPage = () => {
  if (payUrl.value) window.open(payUrl.value, '_blank')
}

const checkOrderStatus = async () => {
  if (!order.value) return
  try {
    const res = await getOrderDetail(order.value.order_no)
    if (res.code === 100) {
      order.value = res.data
      if (order.value.status === 'paid') {
        stopPolling()
        ElMessage.success('支付成功')
      } else if (order.value.status === 'pending') {
        ElMessage.info('订单仍在等待付款')
      }
    }
  } catch (error) {
    ElMessage.error('刷新失败')
  }
}

const startPolling = () => {
  if (pollingTimer.value) return
  pollingTimer.value = setInterval(async () => {
    if (!order.value || order.value.status !== 'pending') {
      stopPolling()
      return
    }
    try {
      const res = await getOrderDetail(order.value.order_no)
      if (res.code === 100) {
        order.value = res.data
        if (order.value.status === 'paid') {
          stopPolling()
          ElMessage.success('支付成功')
        }
      }
    } catch (error) {
      if (error?.response?.status === 401) {
        stopPolling()
        ElMessage.warning('登录已过期，请刷新页面后重新登录')
      }
    }
  }, 3000)
}

const stopPolling = () => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

const handlePay = async () => {
  if (!order.value) return
  payLoading.value = true
  try {
    const res = await payOrder(order.value.id)
    if (res.code === 100) {
      order.value = res.data.order
      payUrl.value = res.data.pay_url
      if (res.data.pay_url) {
        window.open(res.data.pay_url, '_blank')
        startPolling()
      } else {
        ElMessage.error('支付接口暂时不可用')
      }
    }
  } catch (error) {
    ElMessage.error('支付失败，请稍后重试')
  } finally {
    payLoading.value = false
  }
}

const loadOrder = async () => {
  const orderNo = route.params.orderNo
  if (!orderNo) return
  try {
    const res = await getOrderDetail(orderNo)
    if (res.code === 100) {
      order.value = res.data
      if (order.value.status === 'paid' || order.value.status === 'cancelled') return

      if (route.query.out_trade_no) {
        // 支付宝回调回来的，只轮询不重复发起支付
        ElMessage.info('支付完成，等待确认...')
        startPolling()
      } else {
        handlePay()
      }
    }
  } catch (error) {
    console.error('加载订单失败', error)
  }
}

onMounted(() => loadOrder())
onUnmounted(() => stopPolling())
</script>

<style scoped>
.pay-view { padding: 20px; max-width: 600px; margin: 0 auto; }
.pay-card { border-radius: 8px; }
.loading { display: flex; justify-content: center; padding: 40px; }
.pay-content { padding: 20px 0; }
.order-info { background: #fafafa; padding: 16px; border-radius: 8px; }
.info-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.info-row:last-child { margin-bottom: 0; }
.info-row .label { font-size: 14px; color: #606266; }
.info-row .value { font-size: 14px; color: #303133; }
.info-row .value.amount { font-size: 24px; font-weight: 700; color: #f56c6c; }
.info-row .value.status { color: #e6a23c; }
.paid-success, .cancelled { display: flex; flex-direction: column; align-items: center; padding: 40px 0; }
.paid-success h3, .cancelled h3 { margin: 16px 0 8px; font-size: 20px; }
.paid-success p { color: #909399; margin: 0 0 24px; }
.pay-methods { padding: 20px 0; }
.pay-methods h4 { font-size: 16px; margin: 0 0 16px; color: #303133; }
.method-item { margin-bottom: 16px; }
.method-icon { display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; background: #f0f5ff; border-radius: 6px; margin-right: 12px; }
.payment-section { text-align: center; }
.pay-redirect { padding: 20px; background: #f0f5ff; border: 1px dashed #1677ff; border-radius: 8px; margin-bottom: 20px; }
.redirect-tip { color: #1677ff; font-size: 14px; margin: 0 0 16px; }
.polling-hint { display: flex; align-items: center; justify-content: center; gap: 8px; color: #909399; font-size: 14px; margin: 16px 0 0; }
.no-alipay { margin-bottom: 20px; }
.pay-actions { text-align: center; }
</style>

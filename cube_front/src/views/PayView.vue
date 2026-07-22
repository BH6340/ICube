<template>
  <div class="pay-view">
    <el-card shadow="never" class="pay-card">
      <template #header>
        <span>订单支付</span>
      </template>

      <div v-if="!order" class="loading">
        <el-icon size="48" color="#409EFF">
          <Loading />
        </el-icon>
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

        <div v-if="order.status === 'paid'" class="paid-success">
          <el-icon size="48" color="#67c23a">
            <CircleCheck />
          </el-icon>
          <h3>支付成功</h3>
          <p>您的订单已成功支付</p>
          <el-button type="primary" @click="goToOrders">查看订单</el-button>
        </div>

        <div v-else-if="order.status === 'cancelled'" class="cancelled">
          <el-icon size="48" color="#f56c6c">
            <CircleClose />
          </el-icon>
          <h3>订单已取消</h3>
          <el-button type="primary" @click="goToOrders">查看订单</el-button>
        </div>

        <div v-else class="pay-methods">
          <h4>选择支付方式</h4>

          <div class="method-item">
            <el-radio v-model="selectedMethod" value="alipay">
              <div class="method-icon">
                <el-icon size="24" color="#1677ff">
                  <CreditCard />
                </el-icon>
              </div>
              <span>支付宝支付</span>
            </el-radio>
          </div>

          <div v-if="payUrl || qrCodeUrl" class="payment-section">
            <!-- 网页支付 -->


            <div v-if="payUrl" class="pay-redirect">
              <p class="redirect-tip">扫码支付最稳定，也可点击按钮在新窗口支付</p>
              <el-button type="default" @click="goToPayPage">
                在浏览器中打开支付页面
              </el-button>
            </div>

            <!-- 扫码支付 -->
            <div v-if="qrCodeUrl" class="qr-code-section">
              <div class="qr-code">
                <canvas ref="qrCanvas"></canvas>
              </div>
              <p class="qr-tip">使用支付宝扫码支付</p>
            </div>

            <p class="polling-hint">
              <el-icon><Loading /></el-icon>
              等待支付结果...
            </p>
          </div>

          <div v-else class="no-alipay">
            <el-alert
              title="支付接口异常"
              description="支付宝支付接口暂时不可用，请稍后重试"
              type="error"
              show-icon
            />
          </div>

          <div class="pay-actions">
            <el-button type="primary" size="large" :loading="payLoading" @click="handlePay" :disabled="!!(payUrl || qrCodeUrl)">
              {{ payLoading ? '支付中...' : '立即支付' }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, CircleClose, CreditCard, Loading } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { getOrderDetail, payOrder } from '@/api/shop'

const route = useRoute()
const router = useRouter()
const order = ref(null)
const qrCodeUrl = ref(null)
const payUrl = ref(null)
const payLoading = ref(false)
const selectedMethod = ref('alipay')
const pollingTimer = ref(null)
const qrCanvas = ref(null)

const getStatusText = (status) => {
  const statusMap = {
    pending: '待付款',
    paid: '已付款',
    shipped: '已发货',
    completed: '已完成',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const goToOrders = () => {
  router.push('/profiles/orders')
}

const goToPayPage = () => {
  if (payUrl.value) {
    window.open(payUrl.value, '_blank')
  }
}

const drawQRCode = (text) => {
  if (!qrCanvas.value || !text) return

  const canvas = qrCanvas.value
  const ctx = canvas.getContext('2d')
  const size = 200
  canvas.width = size
  canvas.height = size

  // 使用 qrserver API 生成真实 QR 码图片
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    ctx.clearRect(0, 0, size, size)
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, size, size)
    ctx.drawImage(img, 0, 0, size, size)
  }
  img.onerror = () => {
    ctx.fillStyle = '#f0f0f0'
    ctx.fillRect(0, 0, size, size)
    ctx.fillStyle = '#999'
    ctx.font = '14px Arial'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('二维码加载失败', size / 2, size / 2)
  }
  img.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(text)}`
}

const startPolling = () => {
  if (pollingTimer.value) return
  
  pollingTimer.value = setInterval(async () => {
    if (!order.value || order.value.status === 'paid') {
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
      console.error('轮询订单状态失败', error)
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
      qrCodeUrl.value = res.data.qr_code

      if (res.data.pay_url || res.data.qr_code) {
        ElMessage.success('请扫描二维码或点击按钮支付')
        nextTick(() => {
          if (res.data.qr_code) drawQRCode(res.data.qr_code)
        })
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
      if (order.value.status === 'pending') {
        handlePay()
      }
    }
  } catch (error) {
    console.error('加载订单失败', error)
  }
}

onMounted(() => {
  loadOrder()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.pay-view {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.pay-card {
  border-radius: 8px;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.pay-content {
  padding: 20px 0;
}

.order-info {
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  font-size: 14px;
  color: #606266;
}

.info-row .value {
  font-size: 14px;
  color: #303133;
}

.info-row .value.amount {
  font-size: 24px;
  font-weight: 700;
  color: #f56c6c;
}

.info-row .value.status {
  color: #e6a23c;
}

.paid-success,
.cancelled {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
}

.paid-success h3,
.cancelled h3 {
  margin: 16px 0 8px;
  font-size: 20px;
}

.paid-success p {
  color: #909399;
  margin: 0 0 24px;
}

.pay-methods {
  padding: 20px 0;
}

.pay-methods h4 {
  font-size: 16px;
  margin: 0 0 16px;
  color: #303133;
}

.method-item {
  margin-bottom: 16px;
}

.method-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: #f0f5ff;
  border-radius: 6px;
  margin-right: 12px;
}

.qr-code-section {
  text-align: center;
  padding: 20px;
  background: #fff;
  border: 1px dashed #e4e7ed;
  border-radius: 8px;
  margin-bottom: 20px;
}

.qr-code {
  width: 200px;
  height: 200px;
  background: #fff;
  margin: 0 auto;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.qr-code img {
  width: 100%;
  height: 100%;
}

.qr-tip {
  margin: 12px 0 0;
  color: #909399;
  font-size: 14px;
}

.payment-section {
  text-align: center;
}

.pay-redirect {
  padding: 20px;
  background: #f0f5ff;
  border: 1px dashed #1677ff;
  border-radius: 8px;
  margin-bottom: 20px;
}

.redirect-tip {
  color: #1677ff;
  font-size: 14px;
  margin: 0 0 16px;
}

.polling-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #909399;
  font-size: 14px;
  margin: 16px 0 0;
}

.no-alipay {
  margin-bottom: 20px;
}

.pay-actions {
  text-align: center;
}
</style>
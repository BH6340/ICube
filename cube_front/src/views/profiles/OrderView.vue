<template>
  <div class="order-view">
    <el-card shadow="never" class="order-card">
      <template #header>
        <div class="header-wrapper">
          <span>我的订单</span>
          <el-tabs v-model="activeTab" class="order-tabs">
            <el-tab-pane label="全部" name="all" />
            <el-tab-pane label="待付款" name="pending" />
            <el-tab-pane label="已付款" name="paid" />
            <el-tab-pane label="已发货" name="shipped" />
            <el-tab-pane label="已完成" name="completed" />
            <el-tab-pane label="已取消" name="cancelled" />
          </el-tabs>
        </div>
      </template>

      <div v-if="orderList.length > 0" class="order-list">
        <div v-for="order in orderList" :key="order.id" class="order-item">
          <div class="order-header">
            <span class="order-no">订单号: {{ order.order_no }}</span>
            <el-tag :type="getStatusType(order.status)" size="small">{{ getStatusLabel(order.status) }}</el-tag>
          </div>
          
          <div class="order-items">
            <div v-for="item in order.items" :key="item.id" class="order-item-row">
              <div class="item-image">
                <img v-if="item.product_image" :src="item.product_image" :alt="item.product_name" />
                <div v-else class="placeholder">
                  <el-icon size="24" color="#ccc">
                    <ShoppingBag />
                  </el-icon>
                </div>
              </div>
              <div class="item-info">
                <h4 class="item-name">{{ item.product_name }}</h4>
                <span class="item-spec" v-if="item.selected_spec && Object.keys(item.selected_spec).length">
                  {{ formatSpec(item.selected_spec) }}
                </span>
                <div class="item-price-row">
                  <span class="item-price">¥{{ item.price }}</span>
                  <span class="item-quantity">x{{ item.quantity }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="order-footer">
            <span class="total">合计: <span class="total-price">¥{{ order.total_amount }}</span></span>
            <div class="order-actions">
              <el-button v-if="order.status === 'pending'" type="primary" @click="handlePay(order)">支付</el-button>
              <el-button v-if="order.status === 'pending' || order.status === 'paid'" type="info" @click="handleCancel(order)">取消</el-button>
              <el-button v-if="order.status === 'shipped'" type="primary" @click="handleComplete(order)">确认收货</el-button>
              <el-button v-if="order.status === 'completed'" type="default" disabled>已完成</el-button>
            </div>
          </div>
        </div>
      </div>

      <el-empty v-else description="暂无订单" :image-size="80" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ShoppingBag } from '@element-plus/icons-vue'
import { getOrders, payOrder, cancelOrder, completeOrder } from '@/api/shop'

const activeTab = ref('all')
const orderList = ref([])

const statusLabels = {
  pending: '待付款',
  paid: '已付款',
  shipped: '已发货',
  completed: '已完成',
  cancelled: '已取消'
}

const statusTypes = {
  pending: 'warning',
  paid: 'primary',
  shipped: 'info',
  completed: 'success',
  cancelled: 'danger'
}

const getStatusLabel = (status) => {
  return statusLabels[status] || status
}

const getStatusType = (status) => {
  return statusTypes[status] || 'default'
}

const formatSpec = (spec) => {
  return Object.entries(spec).map(([k, v]) => `${k}: ${v}`).join(' / ')
}

const handlePay = async (order) => {
  try {
    const res = await payOrder(order.id)
    if (res.code === 100) {
      ElMessage.success('支付成功')
      loadOrders()
    }
  } catch (error) {
    ElMessage.error('支付失败')
  }
}

const handleCancel = async (order) => {
  try {
    const res = await cancelOrder(order.id)
    if (res.code === 100) {
      ElMessage.success('取消成功')
      loadOrders()
    }
  } catch (error) {
    ElMessage.error('取消失败')
  }
}

const handleComplete = async (order) => {
  try {
    const res = await completeOrder(order.id)
    if (res.code === 100) {
      ElMessage.success('确认收货成功')
      loadOrders()
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const loadOrders = async () => {
  const params = {}
  if (activeTab.value !== 'all') {
    params.status = activeTab.value
  }
  try {
    const res = await getOrders(params)
    if (res.code === 100) {
      orderList.value = res.data.results || res.data
    }
  } catch (error) {
    ElMessage.error('加载订单失败')
  }
}

watch(activeTab, () => {
  loadOrders()
})

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.order-view {
  padding: 20px;
}

.order-card {
  border-radius: 8px;
}

.header-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-tabs {
  margin-bottom: 0;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
}

.order-no {
  font-size: 14px;
  color: #606266;
}

.order-items {
  padding: 12px 16px;
}

.order-item-row {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed #e4e7ed;
}

.order-item-row:last-child {
  border-bottom: none;
}

.item-image {
  width: 80px;
  height: 80px;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-image .placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 4px 0;
}

.item-spec {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.item-price-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-price {
  font-size: 14px;
  font-weight: 600;
  color: #f56c6c;
}

.item-quantity {
  font-size: 13px;
  color: #909399;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
}

.total {
  font-size: 14px;
  color: #606266;
}

.total-price {
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
}

.order-actions {
  display: flex;
  gap: 8px;
}
</style>
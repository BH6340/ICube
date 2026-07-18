<template>
  <div class="checkout-view">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="16">
        <el-card shadow="never" class="address-card">
          <template #header>
            <span>收货地址</span>
          </template>
          <el-form :model="addressForm" label-position="top" class="address-form">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="收货人">
                  <el-input v-model="addressForm.name" placeholder="请输入收货人姓名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="联系电话">
                  <el-input v-model="addressForm.phone" placeholder="请输入联系电话" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="详细地址">
              <el-input v-model="addressForm.detail" placeholder="请输入详细地址" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" class="order-card">
          <template #header>
            <span>商品清单</span>
          </template>
          <div v-if="cartList.length > 0" class="order-items">
            <div v-for="item in cartList" :key="item.id" class="order-item">
              <div class="item-image">
                <img v-if="item.product_info.thumbnail" :src="item.product_info.thumbnail" :alt="item.product_info.name" />
                <div v-else class="placeholder">
                  <el-icon size="24" color="#ccc">
                    <ShoppingBag />
                  </el-icon>
                </div>
              </div>
              <div class="item-info">
                <h4 class="item-name">{{ item.product_info.name }}</h4>
                <span class="item-spec" v-if="item.selected_spec && Object.keys(item.selected_spec).length">
                  {{ formatSpec(item.selected_spec) }}
                </span>
              </div>
              <div class="item-price">¥{{ item.product_info.price }}</div>
              <div class="item-quantity">x{{ item.quantity }}</div>
              <div class="item-total">¥{{ (item.product_info.price * item.quantity).toFixed(2) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="summary-card">
          <template #header>
            <span>订单摘要</span>
          </template>
          <div class="summary-content">
            <div class="summary-row">
              <span class="label">商品数量:</span>
              <span class="value">{{ totalQuantity }} 件</span>
            </div>
            <div class="summary-row">
              <span class="label">商品金额:</span>
              <span class="value">¥{{ totalPrice.toFixed(2) }}</span>
            </div>
            <div class="summary-row">
              <span class="label">运费:</span>
              <span class="value">¥0.00</span>
            </div>
            <el-divider style="margin: 12px 0;" />
            <div class="summary-row total">
              <span class="label">实付款:</span>
              <span class="value">¥{{ totalPrice.toFixed(2) }}</span>
            </div>
          </div>
          <div class="checkout-actions">
            <el-button type="primary" size="large" @click="handleSubmit">提交订单</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { ShoppingBag } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { getCart, createOrder } from '@/api/shop'

const route = useRoute()
const router = useRouter()
const cartList = ref([])
const addressForm = reactive({
  name: '',
  phone: '',
  detail: ''
})

const totalQuantity = computed(() => {
  return cartList.value.reduce((sum, item) => sum + item.quantity, 0)
})

const totalPrice = computed(() => {
  return cartList.value.reduce((total, item) => {
    return total + item.product_info.price * item.quantity
  }, 0)
})

const formatSpec = (spec) => {
  return Object.entries(spec).map(([k, v]) => `${k}: ${v}`).join(' / ')
}

const handleSubmit = async () => {
  if (!addressForm.name || !addressForm.phone || !addressForm.detail) {
    ElMessage.error('请填写完整的收货地址')
    return
  }

  const cartIds = cartList.value.map(item => item.id)
  if (cartIds.length === 0) {
    ElMessage.error('购物车为空')
    return
  }

  try {
    const res = await createOrder({
      cart_ids: cartIds,
      address: { ...addressForm }
    })
    if (res.code === 100) {
      ElMessage.success('下单成功')
      router.push(`/shop/pay/${res.data.order_no}`)
    }
  } catch (error) {
    ElMessage.error('下单失败')
  }
}

const loadCart = async () => {
  try {
    const res = await getCart()
    if (res.code === 100) {
      cartList.value = res.data.results || res.data
    }
  } catch (error) {
    console.error('加载购物车失败', error)
  }
}

onMounted(() => {
  loadCart()
})
</script>

<style scoped>
.checkout-view {
  padding: 20px;
}

.address-card,
.order-card,
.summary-card {
  border-radius: 8px;
  margin-bottom: 16px;
}

.address-form {
  padding: 10px 0;
}

.order-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px dashed #e4e7ed;
  gap: 12px;
}

.order-item:last-child {
  border-bottom: none;
}

.item-image {
  width: 60px;
  height: 60px;
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
  gap: 4px;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0;
}

.item-spec {
  font-size: 12px;
  color: #909399;
}

.item-price {
  font-size: 14px;
  font-weight: 600;
  color: #f56c6c;
  width: 80px;
}

.item-quantity {
  font-size: 13px;
  color: #909399;
  width: 50px;
  text-align: center;
}

.item-total {
  font-size: 14px;
  font-weight: 600;
  color: #f56c6c;
  width: 80px;
  text-align: right;
}

.summary-content {
  padding: 10px 0;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.summary-row .label {
  font-size: 14px;
  color: #606266;
}

.summary-row .value {
  font-size: 14px;
  color: #303133;
}

.summary-row.total .label {
  font-size: 16px;
  font-weight: 600;
}

.summary-row.total .value {
  font-size: 20px;
  font-weight: 700;
  color: #f56c6c;
}

.checkout-actions {
  padding-top: 10px;
}
</style>
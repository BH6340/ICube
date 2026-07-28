<template>
  <div class="checkout-view">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="16">
        <el-card shadow="never" class="address-card">
          <template #header>
            <span>收货地址</span>
            <el-button size="small" type="primary" icon="Plus" @click="goToAddressManage">
              管理地址
            </el-button>
          </template>

          <div v-if="addresses.length > 0" class="address-selector">
            <div
              v-for="address in addresses"
              :key="address.id"
              class="address-option"
              :class="{ 'selected': selectedAddressId === address.id }"
              @click="selectAddress(address)"
            >
              <el-radio :value="address.id" v-model="selectedAddressId" />
              <div class="address-info">
                <div class="address-header-row">
                  <span class="address-name">{{ address.name }}</span>
                  <span class="address-phone">{{ address.phone }}</span>
                  <el-tag v-if="address.is_default" size="small" type="primary" effect="plain">
                    默认
                  </el-tag>
                </div>
                <div class="address-detail">
                  {{ address.province }}{{ address.city }}{{ address.district }}{{ address.detail }}
                </div>
              </div>
            </div>
          </div>

          <el-divider v-if="addresses.length > 0" style="margin: 16px 0;" />

          <el-form :model="addressForm" label-position="top" class="address-form">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="收货人" prop="name">
                  <el-input v-model="addressForm.name" placeholder="请输入收货人姓名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="联系电话" prop="phone">
                  <el-input v-model="addressForm.phone" placeholder="请输入联系电话" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item label="省份" prop="province">
                  <el-input v-model="addressForm.province" placeholder="请输入省份" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="城市" prop="city">
                  <el-input v-model="addressForm.city" placeholder="请输入城市" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="区县" prop="district">
                  <el-input v-model="addressForm.district" placeholder="请输入区县" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="详细地址" prop="detail">
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
/**
 * CheckoutView.vue - 结算页面
 *
 * 核心职责：
 * 1. 展示购物车选中商品结算信息
 * 2. 选择收货地址或新增地址
 * 3. 提交订单创建请求
 *
 * 功能特性：
 *   - 地址列表展示和选择
 *   - 支持新增地址对话框
 *   - 订单金额明细（商品总额、运费）
 *   - 提交前校验地址选择
 *
 * 设计要点：
 *   - addressForm 使用 reactive 存储新地址表单
 *   - 从路由参数获取要结算的购物车 ID 列表
 *   - 订单创建成功后跳转到支付页面
 */
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { ShoppingBag } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { getCart, createOrder, getAddresses } from '@/api/shop'

const route = useRoute()
const router = useRouter()
const cartList = ref([])
const addresses = ref([])
const selectedAddressId = ref(null)

const addressForm = reactive({
  name: '',
  phone: '',
  province: '',
  city: '',
  district: '',
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

const selectAddress = (address) => {
  selectedAddressId.value = address.id
  addressForm.name = address.name
  addressForm.phone = address.phone
  addressForm.province = address.province
  addressForm.city = address.city
  addressForm.district = address.district
  addressForm.detail = address.detail
}

const goToAddressManage = () => {
  router.push('/profiles/addresses')
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

const loadAddresses = async () => {
  try {
    const res = await getAddresses()
    if (res.code === 100) {
      addresses.value = res.data || []
      const defaultAddress = addresses.value.find(a => a.is_default)
      if (defaultAddress) {
        selectAddress(defaultAddress)
      }
    }
  } catch (error) {
    console.error('加载地址列表失败', error)
  }
}

onMounted(() => {
  loadCart()
  loadAddresses()
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

.address-card :deep(.el-card__header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.address-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.address-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 2px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.address-option:hover {
  border-color: #c0c4cc;
}

.address-option.selected {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.address-option .address-info {
  flex: 1;
}

.address-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.address-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.address-phone {
  font-size: 13px;
  color: #606266;
}

.address-detail {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
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
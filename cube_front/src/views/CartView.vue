<template>
  <div class="cart-view">
    <el-card shadow="never" class="cart-card">
      <template #header>
        <span>我的购物车</span>
      </template>

      <div v-if="cartList.length > 0" class="cart-list">
        <div v-for="item in cartList" :key="item.id" class="cart-item">
          <el-checkbox v-model="selectedCartIds" :value="item.id" />
          <div class="item-image" @click="goToProduct(item.product_info)">
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
            <div class="item-price">¥{{ item.product_info.price }}</div>
          </div>
          <div class="item-quantity">
            <el-input-number
              v-model="item.quantity"
              :min="1"
              :max="item.product_info.stock"
              size="small"
              @change="handleQuantityChange(item)"
            />
          </div>
          <div class="item-total">¥{{ (item.product_info.price * item.quantity).toFixed(2) }}</div>
          <div class="item-delete">
            <el-button type="text" @click="handleDelete(item)">删除</el-button>
          </div>
        </div>
      </div>

      <el-empty v-else description="购物车为空" :image-size="80" />

      <div v-if="cartList.length > 0" class="cart-footer">
        <div class="select-all">
          <el-checkbox v-model="selectAll" @change="handleSelectAll">全选</el-checkbox>
          <span class="selected-count">已选 {{ selectedCartIds.length }} 件</span>
        </div>
        <div class="total-section">
          <span class="total-label">合计:</span>
          <span class="total-price">¥{{ totalPrice.toFixed(2) }}</span>
          <el-button type="primary" :disabled="selectedCartIds.length === 0" @click="goToCheckout">
            去结算
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
/**
 * CartView.vue - 购物车页面
 *
 * 核心职责：
 * 1. 展示用户购物车商品列表
 * 2. 支持修改商品数量、删除商品、选择商品
 * 3. 计算选中商品总价，跳转结算
 *
 * 功能特性：
 *   - 全选/反选商品
 *   - 数量加减按钮（最小数量为 1）
 *   - 实时计算总价和总数量
 *   - 删除商品后刷新购物车版本
 *
 * 设计要点：
 *   - 使用 useCartRefresh 跨组件同步购物车状态
 *   - selectedCartIds 存储选中商品 ID 数组
 */
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ShoppingBag } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { getCart, updateCart, deleteCartItem } from '@/api/shop'
import { useCartRefresh } from '@/stores/cart'

const router = useRouter()
const { bumpCartVersion } = useCartRefresh()
const cartList = ref([])
const selectedCartIds = ref([])

const selectAll = computed({
  get() {
    return cartList.value.length > 0 && cartList.value.every(item => selectedCartIds.value.includes(item.id))
  },
  set(val) {
    if (val) {
      selectedCartIds.value = cartList.value.map(item => item.id)
    } else {
      selectedCartIds.value = []
    }
  }
})

const totalPrice = computed(() => {
  return selectedCartIds.value.reduce((total, cartId) => {
    const item = cartList.value.find(c => c.id === cartId)
    if (item) {
      return total + item.product_info.price * item.quantity
    }
    return total
  }, 0)
})

const formatSpec = (spec) => {
  return Object.entries(spec).map(([k, v]) => `${k}: ${v}`).join(' / ')
}

const handleQuantityChange = async (item) => {
  try {
    await updateCart(item.id, { quantity: item.quantity })
    bumpCartVersion()
  } catch (error) {
    ElMessage.error('更新数量失败')
  }
}

const handleDelete = async (item) => {
  try {
    await deleteCartItem(item.id)
    cartList.value = cartList.value.filter(c => c.id !== item.id)
    selectedCartIds.value = selectedCartIds.value.filter(id => id !== item.id)
    bumpCartVersion()
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleSelectAll = () => {}

const goToProduct = (product) => {
  router.push(`/shop?product=${product.id}`)
}

const goToCheckout = () => {
  router.push({
    path: '/shop/checkout',
    query: { cart_ids: selectedCartIds.value.join(',') }
  })
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
.cart-view {
  padding: 20px;
}

.cart-card {
  border-radius: 8px;
}

.cart-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cart-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  gap: 16px;
}

.item-image {
  width: 80px;
  height: 80px;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
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
}

.item-quantity {
  width: 100px;
}

.item-total {
  width: 100px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: #f56c6c;
}

.item-delete {
  width: 60px;
}

.cart-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  margin-top: 16px;
}

.select-all {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-count {
  font-size: 14px;
  color: #606266;
}

.total-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.total-label {
  font-size: 14px;
  color: #606266;
}

.total-price {
  font-size: 20px;
  font-weight: 700;
  color: #f56c6c;
}
</style>
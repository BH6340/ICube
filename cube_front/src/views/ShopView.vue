<template>
  <div class="shop-view">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="8" :md="6">
        <div class="sidebar">
          <el-card shadow="never" class="category-card">
            <template #header>
              <span>商品分类</span>
            </template>
            <el-tree :data="categoryTree" :props="{ label: 'name', children: 'children' }"
              :expand-on-click-node="false" :highlight-current="true"
              @node-click="handleCategoryClick" default-expand-all />
          </el-card>

          <el-card shadow="never" class="price-card">
            <template #header>
              <span>价格区间</span>
            </template>
            <el-form :inline="true" class="price-form">
              <el-form-item>
                <el-input v-model="priceMin" placeholder="最低价" size="small" />
              </el-form-item>
              <span>-</span>
              <el-form-item>
                <el-input v-model="priceMax" placeholder="最高价" size="small" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="small" @click="handlePriceFilter">筛选</el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <el-card shadow="never" class="search-card">
            <template #header>
              <span>搜索商品</span>
            </template>
            <el-input v-model="searchKeyword" placeholder="输入商品名称" prefix-icon="Search" clearable
              @keyup.enter="handleSearch" @clear="handleSearch" @input="handleSearch" />
          </el-card>
        </div>
      </el-col>

      <el-col :xs="24" :sm="16" :md="18">
        <div class="main-content">
          <div class="toolbar">
            <span class="result-count">共 {{ total }} 件商品</span>
            <el-select v-model="sortBy" @change="handleSortChange" style="width: 120px">
              <el-option label="默认排序" value="default" />
              <el-option label="价格升序" value="price_asc" />
              <el-option label="价格降序" value="price_desc" />
              <el-option label="销量优先" value="sales" />
            </el-select>
          </div>

          <div class="product-grid">
            <el-card v-for="product in productList" :key="product.id" class="product-card"
              @click="handleProductClick(product)" hover>
              <div class="product-image">
                <img v-if="product.thumbnail" :src="product.thumbnail" :alt="product.name" />
                <div v-else class="placeholder">
                  <el-icon size="48" color="#ccc">
                    <ShoppingBag />
                  </el-icon>
                </div>
              </div>
              <div class="product-info">
                <h3 class="product-name">{{ product.name }}</h3>
                <p class="product-desc">{{ product.description }}</p>
                <div class="product-price">
                  <span class="current-price">¥{{ product.price }}</span>
                  <span v-if="product.original_price" class="original-price">¥{{ product.original_price }}</span>
                </div>
                <div class="product-meta">
                  <span class="sales">销量: {{ product.sales_count }}</span>
                  <span class="stock">库存: {{ product.stock }}</span>
                </div>
              </div>
              <div class="product-actions">
                <el-button type="primary" size="small" @click.stop="handleAddToCart(product)">
                  <el-icon><ShoppingCart /></el-icon>
                  加入购物车
                </el-button>
              </div>
            </el-card>
          </div>

          <div v-if="total > pageSize" class="pagination-wrapper">
            <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total"
              layout="total, prev, pager, next" @current-change="handlePageChange" />
          </div>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="showDetailDialog" :title="selectedProduct?.name" width="800px">
      <div v-if="selectedProduct" class="product-detail">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="10">
            <div class="detail-images">
              <el-carousel height="300px" indicator-position="bottom">
                <el-carousel-item v-for="(img, idx) in productImages" :key="idx">
                  <img :src="img" :alt="selectedProduct.name" class="carousel-img" />
                </el-carousel-item>
              </el-carousel>
            </div>
          </el-col>
          <el-col :xs="24" :sm="14">
            <div class="detail-info">
              <div class="detail-price">
                <span class="current">¥{{ selectedProduct.price }}</span>
                <span v-if="selectedProduct.original_price" class="original">¥{{ selectedProduct.original_price }}</span>
              </div>
              <div class="detail-stats">
                <span>销量: {{ selectedProduct.sales_count }}</span>
                <span>库存: {{ selectedProduct.stock }}</span>
              </div>
              <div v-if="selectedProduct.specs && Object.keys(selectedProduct.specs).length" class="detail-specs">
                <span class="spec-label">规格:</span>
                <div v-for="(values, key) in selectedProduct.specs" :key="key" class="spec-row">
                  <span class="spec-name">{{ key }}:</span>
                  <el-button-group>
                    <el-button
                      v-for="val in values"
                      :key="val"
                      :type="selectedSpec[key] === val ? 'primary' : 'default'"
                      size="small"
                      @click="selectedSpec[key] = val"
                    >{{ val }}</el-button>
                  </el-button-group>
                </div>
              </div>
              <div class="detail-quantity">
                <span>数量:</span>
                <el-input-number
                  v-model="quantity"
                  :min="1"
                  :max="selectedProduct.stock"
                  size="small"
                />
              </div>
              <div class="detail-desc">
                <p>{{ selectedProduct.description }}</p>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleAddToCart(selectedProduct)">
          <el-icon><ShoppingCart /></el-icon>
          加入购物车
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { ShoppingBag, ShoppingCart } from '@element-plus/icons-vue'
import { getCategories, getProducts, getProductDetail, addToCart } from '@/api/shop'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const categoryTree = ref([])
const productList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const selectedCategory = ref(null)
const searchKeyword = ref('')
const sortBy = ref('default')
const priceMin = ref('')
const priceMax = ref('')
const showDetailDialog = ref(false)
const selectedProduct = ref(null)
const quantity = ref(1)
const selectedSpec = reactive({})

const productImages = computed(() => {
  if (!selectedProduct.value) return []
  const images = selectedProduct.value.images || []
  const thumbnail = selectedProduct.value.thumbnail
  if (thumbnail && !images.includes(thumbnail)) {
    return [thumbnail, ...images]
  }
  return images.length ? images : (thumbnail ? [thumbnail] : [])
})

const handleCategoryClick = (data) => {
  selectedCategory.value = data.id
  currentPage.value = 1
  loadProducts()
}

const handlePriceFilter = () => {
  currentPage.value = 1
  loadProducts()
}

const handleSearch = () => {
  currentPage.value = 1
  loadProducts()
}

const handleSortChange = () => {
  currentPage.value = 1
  loadProducts()
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadProducts()
}

const handleProductClick = async (product) => {
  try {
    const res = await getProductDetail(product.id)
    if (res.code === 100) {
      selectedProduct.value = res.data
      quantity.value = 1
      Object.keys(selectedSpec).forEach(key => delete selectedSpec[key])
      if (selectedProduct.value.specs) {
        Object.keys(selectedProduct.value.specs).forEach(key => {
          const values = selectedProduct.value.specs[key]
          if (values && values.length) {
            selectedSpec[key] = values[0]
          }
        })
      }
      showDetailDialog.value = true
    }
  } catch (error) {
    ElMessage.error('加载商品详情失败')
  }
}

const handleAddToCart = async (product) => {
  if (!product) return
  if (!userStore.token) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    const data = {
      product: product.id,
      quantity: quantity.value,
      selected_spec: { ...selectedSpec }
    }
    const res = await addToCart(data)
    if (res.code === 100) {
      ElMessage.success('添加购物车成功')
      showDetailDialog.value = false
      loadProducts()
    }
  } catch (error) {
    ElMessage.error('添加购物车失败')
  }
}

const loadCategories = async () => {
  try {
    const res = await getCategories()
    if (res.code === 100) {
      categoryTree.value = res.data
    }
  } catch (error) {
    ElMessage.error('加载分类失败')
  }
}

const loadProducts = async () => {
  const params = {
    page: currentPage.value,
    page_size: pageSize.value
  }
  if (selectedCategory.value) {
    params.category = selectedCategory.value
  }
  if (searchKeyword.value.trim()) {
    params.keyword = searchKeyword.value.trim()
  }
  if (priceMin.value) {
    params.price_min = priceMin.value
  }
  if (priceMax.value) {
    params.price_max = priceMax.value
  }
  if (sortBy.value !== 'default') {
    if (sortBy.value === 'price_asc') {
      params.sort = 'price'
    } else if (sortBy.value === 'price_desc') {
      params.sort = '-price'
    } else if (sortBy.value === 'sales') {
      params.sort = '-sales_count'
    }
  }
  try {
    const res = await getProducts(params)
    if (res.code === 100) {
      productList.value = res.data.results
      total.value = res.data.count
    }
  } catch (error) {
    ElMessage.error('加载商品失败')
  }
}

onMounted(() => {
  loadCategories()
  loadProducts()
})
</script>

<style scoped>
.shop-view {
  padding: 20px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-card,
.price-card,
.search-card {
  border-radius: 8px;
}

.price-form {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.result-count {
  font-size: 14px;
  color: #606266;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.product-card {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 8px;
  overflow: hidden;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.product-image {
  width: 100%;
  height: 180px;
  background: #f5f7fa;
  overflow: hidden;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-image .placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.product-info {
  padding: 12px;
}

.product-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-desc {
  font-size: 13px;
  color: #909399;
  margin: 0 0 10px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}

.current-price {
  font-size: 18px;
  font-weight: 700;
  color: #f56c6c;
}

.original-price {
  font-size: 13px;
  color: #909399;
  text-decoration: line-through;
}

.product-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.product-actions {
  padding: 0 12px 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.product-detail {
  padding: 10px;
}

.detail-images {
  border-radius: 8px;
  overflow: hidden;
}

.carousel-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-price {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.detail-price .current {
  font-size: 28px;
  font-weight: 700;
  color: #f56c6c;
}

.detail-price .original {
  font-size: 14px;
  color: #909399;
  text-decoration: line-through;
}

.detail-stats {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #606266;
}

.detail-specs {
  padding-top: 10px;
  border-top: 1px solid #e4e7ed;
}

.spec-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.spec-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.spec-name {
  font-size: 13px;
  color: #909399;
  min-width: 60px;
}

.detail-quantity {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #606266;
}

.detail-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.detail-desc p {
  margin: 0;
}
</style>
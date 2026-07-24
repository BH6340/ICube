<template>
  <div class="address-container">
    <div class="address-header">
      <h2 class="address-title">收货地址管理</h2>
      <el-button type="primary" icon="Plus" @click="openAddDialog">
        添加新地址
      </el-button>
    </div>

    <div v-if="addresses.length > 0" class="address-list">
      <div
        v-for="address in addresses"
        :key="address.id"
        class="address-card"
        :class="{ 'active-address': selectedAddressId === address.id }"
        @click="selectAddress(address)"
      >
        <div class="address-radio">
          <el-radio :value="address.id" v-model="selectedAddressId" />
        </div>
        <div class="address-content">
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
        <div class="address-actions">
          <el-button size="small" @click.stop="editAddress(address)">编辑</el-button>
          <el-button size="small" type="danger" @click.stop="deleteAddress(address)">删除</el-button>
          <el-button
            v-if="!address.is_default"
            size="small"
            type="warning"
            @click.stop="handleSetDefault(address)"
          >
            设为默认
          </el-button>
        </div>
      </div>
    </div>

    <el-empty v-else description="暂无收货地址，点击上方按钮添加" :image-size="80" />

    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑地址' : '添加新地址'" width="500px" append-to-body>
      <el-form :model="addressForm" label-position="top" :rules="formRules" ref="addressFormRef">
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
          <el-input
            v-model="addressForm.detail"
            type="textarea"
            :rows="3"
            placeholder="请输入详细地址"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="addressForm.is_default">设为默认地址</el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false" :disabled="loading">取消</el-button>
        <el-button type="primary" :loading="loading" @click="submitAddress">保存地址</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAddresses, createAddress, updateAddress, deleteAddress as deleteAddressApi, setDefaultAddress } from '@/api/shop'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const addresses = ref([])
const selectedAddressId = ref(null)

const addressFormRef = ref(null)
const addressForm = ref({
  id: null,
  name: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  is_default: false
})

const formRules = {
  name: [{ required: true, message: '请输入收货人姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
  province: [{ required: true, message: '请输入省份', trigger: 'blur' }],
  city: [{ required: true, message: '请输入城市', trigger: 'blur' }],
  district: [{ required: true, message: '请输入区县', trigger: 'blur' }],
  detail: [{ required: true, message: '请输入详细地址', trigger: 'blur' }]
}

const loadAddresses = async () => {
  try {
    loading.value = true
    const res = await getAddresses()
    if (res.code === 100) {
      addresses.value = res.data || []
      const defaultAddress = addresses.value.find(a => a.is_default)
      if (defaultAddress) {
        selectedAddressId.value = defaultAddress.id
      }
    }
  } catch (error) {
    console.error('加载地址列表失败', error)
    ElMessage.error('加载地址失败')
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  isEditing.value = false
  addressForm.value = {
    id: null,
    name: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    detail: '',
    is_default: false
  }
  dialogVisible.value = true
}

const editAddress = (address) => {
  isEditing.value = true
  addressForm.value = {
    id: address.id,
    name: address.name,
    phone: address.phone,
    province: address.province,
    city: address.city,
    district: address.district,
    detail: address.detail,
    is_default: address.is_default
  }
  dialogVisible.value = true
}

const submitAddress = async () => {
  if (!addressFormRef.value) return
  await addressFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      loading.value = true
      const formData = {
        name: addressForm.value.name,
        phone: addressForm.value.phone,
        province: addressForm.value.province,
        city: addressForm.value.city,
        district: addressForm.value.district,
        detail: addressForm.value.detail,
        is_default: addressForm.value.is_default
      }

      if (isEditing.value) {
        await updateAddress(addressForm.value.id, formData)
        ElMessage.success('地址更新成功')
      } else {
        await createAddress(formData)
        ElMessage.success('地址添加成功')
      }

      dialogVisible.value = false
      await loadAddresses()
    } catch (error) {
      console.error('保存地址失败', error)
      ElMessage.error(error.response?.data?.msg || '保存失败')
    } finally {
      loading.value = false
    }
  })
}

const deleteAddress = async (address) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个地址吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteAddressApi(address.id)
    ElMessage.success('地址删除成功')
    await loadAddresses()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除地址失败', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleSetDefault = async (address) => {
  try {
    await setDefaultAddress(address.id)
    ElMessage.success('已设为默认地址')
    await loadAddresses()
  } catch (error) {
    console.error('设置默认地址失败', error)
    ElMessage.error('设置失败')
  }
}

const selectAddress = (address) => {
  selectedAddressId.value = address.id
}

onMounted(() => {
  loadAddresses()
})
</script>

<style scoped>
.address-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.address-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.address-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}

.address-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.address-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border: 2px solid #ebeef5;
  border-radius: 12px;
  background-color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.address-card:hover {
  border-color: #c0c4cc;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.address-card.active-address {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.address-radio {
  padding-top: 4px;
}

.address-content {
  flex: 1;
}

.address-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.address-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.address-phone {
  font-size: 14px;
  color: #606266;
}

.address-detail {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.address-actions {
  display: flex;
  gap: 8px;
}
</style>
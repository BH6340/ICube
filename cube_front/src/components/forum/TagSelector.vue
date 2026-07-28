<!-- src/components/forum/TagSelector.vue -->
<template>
  <div class="tag-selector">
    <el-select
      v-model="selectedTags"
      multiple
      filterable
      placeholder="请选择标签"
      @change="handleChange"
      style="width: 100%"
      :loading="loading"
      clearable
    >
      <el-option
        v-for="tag in tags"
        :key="tag.id"
        :label="tag.name"
        :value="tag.id"
      >
        <el-tag :color="tag.color" size="small" effect="dark" style="color: white; border: none;">
          {{ tag.name }}
        </el-tag>
      </el-option>
    </el-select>

    <div class="selected-tags" v-if="selectedTags.length">
      <span class="label">已选标签：</span>
      <el-tag
        v-for="id in selectedTags"
        :key="id"
        :color="getTagColor(id)"
        closable
        @close="removeTag(id)"
        size="small"
        effect="dark"
        style="color: white; border: none;"
      >
        {{ getTagName(id) }}
      </el-tag>
    </div>

    <div v-if="loadError" class="error-tip">
      <el-alert title="加载标签失败，请刷新重试" type="error" :closable="false" show-icon />
    </div>
  </div>
</template>

<script setup>
/**
 * TagSelector.vue - 标签选择器组件
 *
 * 核心职责：
 * 1. 提供帖子标签的多选功能
 * 2. 支持从后端加载标签列表
 * 3. 通过 v-model 双向绑定选中的标签 ID 数组
 *
 * 功能特性：
 *   - 自动从后端加载标签（getTags API）
 *   - 支持初始化时回显已选标签
 *   - 通过 watch 深度监听 modelValue 变化
 *   - 加载失败时显示错误提示
 *
 * Props:
 *   - modelValue: 已选标签 ID 数组
 *
 * Emits:
 *   - update:modelValue: 标签变化时触发
 *
 * 设计要点：
 *   - 使用 watch 实现双向同步（父组件传值 → 内部状态 → 回写父组件）
 */
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getTags } from '@/api/tags'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const tags = ref([])
const selectedTags = ref([]) // 💡 2. 这里初始为空，交由 watch 去双向同步
const loading = ref(false)
const loadError = ref(false)

// 💡 ✨ 修复核心 1：利用 watch 深度监听父组件传过来的 modelValue 的改变
watch(
  () => props.modelValue,
  (newVal) => {
    // 只有当新旧数据不一致时才同步，防止死循环
    if (JSON.stringify(newVal) !== JSON.stringify(selectedTags.value)) {
      selectedTags.value = newVal ? [...newVal] : []
    }
  },
  { immediate: true, deep: true } // immediate 确保初次进入页面或已有值时能立刻同步
)

const loadTags = async () => {
  loading.value = true
  loadError.value = false
  try {
    const res = await getTags({ page: 1, page_size: 100 })
    console.log('标签加载响应:', res)

    if (res.code === 100) {
      tags.value = res.data?.results || res.results || []
    } else if (res.code === 0) {
      tags.value = res.data?.results || res.results || []
    } else if (Array.isArray(res)) {
      tags.value = res
    } else if (res.results) {
      tags.value = res.results
    } else {
      tags.value = []
    }

    if (tags.value.length === 0) {
      console.warn('没有获取到标签数据')
    }
  } catch (error) {
    console.error('加载标签失败:', error)
    loadError.value = true
    ElMessage.error('加载标签失败，请刷新页面重试')
  } finally {
    loading.value = false
  }
}

const getTagName = (id) => {
  const tag = tags.value.find(t => t.id === id)
  return tag?.name || ''
}

const getTagColor = (id) => {
  const tag = tags.value.find(t => t.id === id)
  return tag?.color || '#409EFF'
}

const handleChange = (val) => {
  emit('update:modelValue', val)
}

// 💡 ✨ 修复核心 2：修正删除标签时的双向绑定逻辑
const removeTag = (id) => {
  const index = selectedTags.value.indexOf(id)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
    // 删掉后一定要把更新后的 selectedTags.value 通知给父组件
    handleChange([...selectedTags.value])
  }
}

onMounted(() => {
  loadTags()
})
</script>

<style scoped>
.tag-selector {
  width: 100%;
}

.selected-tags {
  margin-top: 12px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-tags .label {
  font-size: 14px;
  color: #606266;
}

.error-tip {
  margin-top: 10px;
}
</style>
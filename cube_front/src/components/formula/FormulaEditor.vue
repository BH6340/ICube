<template>
  <div v-if="visible" class="formula-editor-overlay" @click="handleClose">
    <div class="formula-editor" @click.stop>
      <div class="editor-header">
        <h3>{{ isEdit ? '编辑公式' : '上传公式' }}</h3>
        <button class="close-btn" @click="handleClose">×</button>
      </div>

      <div class="editor-body">
        <div class="form-group">
          <label>公式名称 *</label>
          <input 
            v-model="form.name" 
            type="text" 
            placeholder="请输入公式名称"
            class="form-input"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>分类</label>
            <div class="category-selector">
              <select v-model="form.category" class="form-select">
                <option value="">请选择分类</option>
                <optgroup v-if="systemCategories.length" label="系统分类">
                  <option v-for="cat in systemCategories" :key="cat.id" :value="cat.id">
                    {{ cat.name }}
                  </option>
                </optgroup>
                <optgroup v-if="customCategories.length" label="我的自定义分类">
                  <option v-for="cat in customCategories" :key="cat.id" :value="cat.id">
                    {{ cat.name }}
                  </option>
                </optgroup>
              </select>
              <button type="button" class="add-category-btn" @click="showCategoryDialog = true">
                + 新建
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>难度</label>
            <select v-model="form.difficulty" class="form-select">
              <option value="">请选择难度</option>
              <option :value="1">1 - 入门</option>
              <option :value="2">2 - 简单</option>
              <option :value="3">3 - 中等</option>
              <option :value="4">4 - 困难</option>
              <option :value="5">5 - 专家</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>公式记号 *</label>
          <div class="notation-display">
            <input 
              v-model="form.notation" 
              type="text" 
              class="notation-input"
              placeholder="点击下方按钮输入公式，或直接输入公式字符串"
            />
            <button type="button" class="clear-btn" @click="clearNotation" v-if="form.notation">
              清空
            </button>
          </div>

          <div class="notation-keyboard">
            <div class="keyboard-row">
              <button type="button" v-for="key in topRow" :key="key" @click="addNotation(key)" class="key-btn">{{ key }}</button>
            </div>
            <div class="keyboard-row">
              <button type="button" v-for="key in middleRow" :key="key" @click="addNotation(key)" class="key-btn">{{ key }}</button>
            </div>
            <div class="keyboard-row">
              <button type="button" v-for="key in bottomRow" :key="key" @click="addNotation(key)" class="key-btn">{{ key }}</button>
            </div>
            <div class="keyboard-row">
              <button type="button" v-for="key in modifiers" :key="key" @click="addNotation(key)" class="key-btn modifier">{{ key }}</button>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>缩略图</label>
          <div class="image-selector">
            <div class="image-preview" v-if="selectedImageUrl">
              <img :src="selectedImageUrl" alt="预览" />
              <button type="button" class="remove-image" @click="removeImage">×</button>
            </div>
            <div class="image-options" v-else>
              <div class="option-btn" @click="showLibrary = true">
                <span class="icon">📚</span>
                <span>从公式库选择</span>
              </div>
              <div class="option-btn" @click="triggerUpload">
                <span class="icon">📷</span>
                <span>上传图片</span>
              </div>
            </div>
            <input 
              ref="fileInput" 
              type="file" 
              accept="image/*" 
              class="file-input" 
              @change="handleFileSelect"
            />
          </div>
        </div>

        <div class="form-group">
          <label>描述</label>
          <textarea 
            v-model="form.description" 
            rows="3" 
            placeholder="请输入公式描述（可选）"
            class="form-textarea"
          ></textarea>
        </div>

        <div class="editor-actions">
          <button type="button" class="btn-cancel" @click="handleClose">取消</button>
          <button type="button" class="btn-confirm" @click="submitFormula" :disabled="!isValid">
            {{ isEdit ? '保存修改' : '上传公式' }}
          </button>
        </div>
      </div>

      <ImageCropper 
        v-if="showCropper" 
        :image-file="cropperFile" 
        @close="showCropper = false"
        @crop="handleCrop"
      />

      <!-- 自定义分类创建弹窗 -->
      <div class="category-modal" v-if="showCategoryDialog" @click.self="showCategoryDialog = false">
        <div class="category-dialog">
          <div class="dialog-header">
            <h3>创建自定义分类</h3>
            <button type="button" class="close-btn" @click="showCategoryDialog = false">×</button>
          </div>
          <div class="dialog-body">
            <div class="form-group">
              <label>分类名称 *</label>
              <input 
                v-model="newCategory.name" 
                type="text" 
                placeholder="如：我的OLL变体"
                class="form-input"
                maxlength="50"
              />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>阶数</label>
                <select v-model="newCategory.order" class="form-select">
                  <option :value="3">3阶</option>
                  <option :value="4">4阶</option>
                  <option :value="5">5阶</option>
                </select>
              </div>
              <div class="form-group">
                <label>求解方法</label>
                <select v-model="newCategory.method" class="form-select">
                  <option v-for="m in METHOD_OPTIONS" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>阶段</label>
                <select v-model="newCategory.phase" class="form-select" filterable>
                  <option v-for="p in PHASE_OPTIONS" :key="p" :value="p">{{ p }}</option>
                </select>
              </div>
            </div>
          </div>
          <div class="dialog-footer">
            <button type="button" class="btn-cancel" @click="showCategoryDialog = false">取消</button>
            <button type="button" class="btn-confirm" @click="handleCreateCategory" :disabled="submitting">
              {{ submitting ? '创建中...' : '创建' }}
            </button>
          </div>
        </div>
      </div>

      <div class="library-modal" v-if="showLibrary" @click="showLibrary = false">
        <div class="library-content" @click.stop>
          <div class="library-header">
            <h3>选择公式图片</h3>
            <button type="button" class="close-btn" @click="showLibrary = false">×</button>
          </div>
          <div class="library-body">
            <div 
              v-for="formula in libraryFormulas" 
              :key="formula.id" 
              class="library-item"
              @click="selectFromLibrary(formula)"
            >
              <img :src="formula.thumbnail" :alt="formula.name" />
              <span>{{ formula.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * FormulaEditor.vue - 公式编辑器组件
 *
 * 核心职责：
 * 1. 提供公式上传/编辑的表单界面
 * 2. 支持公式记号的可视化键盘输入（点击按钮添加步骤）
 * 3. 支持两种图片来源：本地上传（经裁剪压缩）和公式库选择
 * 4. 自动绑定分类对应的 target_state_id
 *
 * 功能特性：
 *   - 记号输入支持两种方式：键盘点击输入 和 直接文本输入
 *   - 修饰符（' 和 2）自动附加到上一个步骤
 *   - 图片上传使用 ImageCropper 组件进行 1:1 裁剪
 *   - 从公式库选择图片时直接引用原路径，无需重新上传
 *
 * Props:
 *   - visible: 控制编辑器显示/隐藏（必填）
 *   - editFormula: 编辑的公式对象（为空时为创建模式）
 *
 * Emits:
 *   - close: 关闭编辑器
 *   - success: 提交成功
 *
 * 设计要点：
 *   - thumbnail 字段支持两种类型：File 对象（本地上传）和 string（路径引用）
 *   - 提交时根据类型分别映射为 thumbnail_file 或 thumbnail_path 字段
 *   - 分类变更时后端自动绑定对应的 target_state_id
 */

import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import ImageCropper from '../ImageCropper.vue'
import { 
  getFormulaCategories, getFormulaList, createFormula, updateFormula,
  createCategory, METHOD_OPTIONS, PHASE_OPTIONS
} from '@/api/formula'

/** 组件属性定义 */
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  editFormula: {
    type: Object,
    default: null
  }
})

/** 组件事件定义 */
const emit = defineEmits(['close', 'success'])

/** 模板引用 */
const fileInput = ref(null)               // 文件选择器引用

/** 表单数据 */
const form = ref({
  name: '',          // 公式名称
  notation: '',      // 公式记号（空格分隔）
  category: '',      // 分类 ID
  difficulty: '',    // 难度等级
  description: '',   // 公式描述
  thumbnail: null    // 缩略图（File | string）
})

/** 图片预览 URL */
const selectedImageUrl = ref('')
/** 是否显示裁剪组件 */
const showCropper = ref(false)
/** 待裁剪的图片文件 */
const cropperFile = ref(null)
/** 是否显示公式库选择弹窗 */
const showLibrary = ref(false)
/** 分类列表 */
const categories = ref([])
/** 系统分类（只读） */
const systemCategories = ref([])
/** 用户自定义分类 */
const customCategories = ref([])
/** 公式库列表（供选择图片） */
const libraryFormulas = ref([])

/** 分类创建弹窗状态 */
const showCategoryDialog = ref(false)
/** 分类创建提交状态 */
const submitting = ref(false)
/** 新分类表单数据 */
const newCategory = reactive({
  name: '',
  order: 3,
  method: 'CFOP',
  phase: 'OLL'
})
/** 求解方法选项 */
const methodOptions = METHOD_OPTIONS
/** 阶段选项 */
const phaseOptions = PHASE_OPTIONS

/** 是否为编辑模式 */
const isEdit = computed(() => !!props.editFormula)

/** 表单是否有效（名称和记号必填） */
const isValid = computed(() => {
  return form.value.name.trim() && form.value.notation.trim()
})

/** 记号键盘布局：标准层转动 */
const topRow = ['R', 'L', 'U', 'D', 'F', 'B']
/** 记号键盘布局：镜像层转动（小写） */
const middleRow = ['r', 'l', 'u', 'd', 'f', 'b']
/** 记号键盘布局：中层和整体转动 */
const bottomRow = ['M', 'E', 'S', 'x', 'y', 'z']
/** 修饰符：逆时针（'）和 180°（2） */
const modifiers = ["'", '2']

/**
 * 组件挂载生命周期
 *
 * 加载公式分类和公式库列表（用于图片选择）。
 */
onMounted(async () => {
  await loadCategories()
  await loadLibraryFormulas()
})

/**
 * 监听编辑器显示状态
 *
 * 当 visible 变为 true 时：
 *   - 编辑模式：加载已有公式数据到表单
 *   - 创建模式：重置表单为空
 */
watch(() => props.visible, async (val) => {
  if (val) {
    if (isEdit.value && props.editFormula) {
      form.value = {
        name: props.editFormula.name,
        notation: props.editFormula.notation,
        category: props.editFormula.category?.id || '',
        difficulty: props.editFormula.difficulty || '',
        description: props.editFormula.description || '',
        thumbnail: props.editFormula.thumbnail || null
      }
      if (props.editFormula.thumbnail) {
        selectedImageUrl.value = props.editFormula.thumbnail
      }
    } else {
      form.value = {
        name: '',
        notation: '',
        category: '',
        difficulty: '',
        description: '',
        thumbnail: null
      }
      selectedImageUrl.value = ''
    }
  }
})

/**
 * 加载公式分类列表
 *
 * 从后端获取所有分类（含方法、阶段信息），并按系统/自定义分组。
 */
const loadCategories = async () => {
  try {
    const res = await getFormulaCategories()
    const data = res.data?.results || res.data || []
    categories.value = data
    systemCategories.value = data.filter(c => !c.is_custom)
    customCategories.value = data.filter(c => c.is_custom)
  } catch (e) {
    console.error('加载分类失败', e)
  }
}

/**
 * 创建自定义分类
 *
 * 验证表单数据后调用后端接口创建分类，
 * 成功后刷新分类列表并自动选中新分类。
 */
const handleCreateCategory = async () => {
  if (!newCategory.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  submitting.value = true
  try {
    const payload = {
      name: newCategory.name.trim(),
      order: newCategory.order,
      method: newCategory.method,
      phase: newCategory.phase
    }
    const res = await createCategory(payload)
    await loadCategories()
    // 自动选中新创建的分类
    form.value.category = res.data?.id || res.data?.data?.id
    showCategoryDialog.value = false
    ElMessage.success('分类创建成功')
    // 重置表单
    Object.assign(newCategory, { name: '', order: 3, method: 'CFOP', phase: 'OLL' })
  } catch (e) {
    ElMessage.error('创建分类失败')
  } finally {
    submitting.value = false
  }
}

/**
 * 添加公式记号步骤
 *
 * 处理规则：
 *   - 普通步骤（R/L/U/D/F/B 等）：追加到记号字符串末尾，自动加空格
 *   - 修饰符（' 和 2）：附加到上一个步骤末尾，不单独成步
 *     例如："R U" + "'" → "R U'"（而非 "R U '"）
 *
 * @param {string} key - 记号按键值
 */
const addNotation = (key) => {
  if (key === "'" || key === '2') {
    if (!form.value.notation.trim()) return
    const lastStep = form.value.notation.split(/\s+/).pop()
    const lastChar = lastStep.slice(-1)
    if (lastChar !== "'" && lastChar !== '2') {
      const steps = form.value.notation.trim().split(/\s+/)
      steps[steps.length - 1] = lastStep + key
      form.value.notation = steps.join(' ')
    }
  } else {
    form.value.notation += (form.value.notation ? ' ' : '') + key
  }
}

/** 清空公式记号 */
const clearNotation = () => {
  form.value.notation = ''
}

/** 触发文件选择对话框 */
const triggerUpload = () => {
  fileInput.value?.click()
}

/**
 * 处理文件选择
 *
 * 选择图片后自动打开裁剪组件，进行 1:1 裁剪。
 *
 * @param {Event} e - 文件选择事件
 */
const handleFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    cropperFile.value = file
    showCropper.value = true
  }
}

/**
 * 处理裁剪完成
 *
 * 裁剪成功后：
 *   - 将裁剪后的文件设为 thumbnail（File 类型）
 *   - 使用 URL.createObjectURL 生成预览
 *   - 关闭裁剪组件
 *
 * @param {File} croppedFile - 裁剪后的 WebP 文件
 */
const handleCrop = (croppedFile) => {
  form.value.thumbnail = croppedFile
  selectedImageUrl.value = URL.createObjectURL(croppedFile)
  showCropper.value = false
}

/** 移除已选择的图片 */
const removeImage = () => {
  form.value.thumbnail = null
  selectedImageUrl.value = ''
}

/**
 * 加载公式库列表
 *
 * 获取前 100 条公式，用于图片选择弹窗。
 * 优先加载有缩略图的公式。
 */
const loadLibraryFormulas = async () => {
  try {
    const res = await getFormulaList({ page_size: 100 })
    libraryFormulas.value = res.data?.results || []
  } catch (e) {
    console.error('加载公式库失败', e)
  }
}

/**
 * 从公式库选择图片
 *
 * 选中公式后，直接使用该公式的 thumbnail 路径作为图片来源，
 * 不重新上传，避免重复存储。
 *
 * @param {Object} formula - 选中的公式对象
 */
const selectFromLibrary = async (formula) => {
  selectedImageUrl.value = formula.thumbnail
  form.value.thumbnail = formula.thumbnail
  showLibrary.value = false
}

/**
 * 提交公式
 *
 * 根据当前模式调用创建或更新接口。
 *
 * 数据映射规则：
 *   - File 类型 thumbnail → thumbnail_file（本地上传，后端处理压缩）
 *   - string 类型 thumbnail → thumbnail_path（公式库选择，直接引用）
 *
 * 后端处理：
 *   - 自动根据 category_id 绑定 target_state_id
 *   - 自动生成缩略图（如果未提供）
 */
const submitFormula = async () => {
  if (!isValid.value) return

  const formData = new FormData()
  formData.append('name', form.value.name.trim())
  formData.append('notation', form.value.notation.trim())
  
  if (form.value.category) {
    formData.append('category_id', form.value.category)
  }
  if (form.value.difficulty) {
    formData.append('difficulty', form.value.difficulty)
  }
  if (form.value.description) {
    formData.append('description', form.value.description.trim())
  }
  
  if (form.value.thumbnail) {
    if (typeof form.value.thumbnail === 'string') {
      formData.append('thumbnail_path', form.value.thumbnail)
    } else {
      formData.append('thumbnail_file', form.value.thumbnail)
    }
  }

  try {
    if (isEdit.value) {
      await updateFormula(props.editFormula.id, formData)
    } else {
      await createFormula(formData)
    }
    emit('success')
    handleClose()
  } catch (e) {
    console.error('提交失败', e)
  }
}

/**
 * 关闭编辑器并重置表单
 *
 * 清除所有表单数据和图片预览，触发 close 事件。
 */
const handleClose = () => {
  form.value = {
    name: '',
    notation: '',
    category: '',
    difficulty: '',
    description: '',
    thumbnail: null
  }
  selectedImageUrl.value = ''
  emit('close')
}
</script>

<style scoped>
.formula-editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  overflow-y: auto;
}

.formula-editor {
  width: 600px;
  max-width: 95%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  margin: 20px 0;
}

.editor-header {
  height: 50px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #eee;
}

.editor-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.close-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
}

.editor-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #333;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-textarea {
  resize: vertical;
}

.form-row {
  display: flex;
  gap: 15px;
}

.form-row .form-group {
  flex: 1;
}

.notation-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #f9f9f9;
}

.notation-input {
  flex: 1;
  font-family: monospace;
  font-size: 16px;
  color: #333;
  border: none;
  background: transparent;
  outline: none;
}

.clear-btn {
  padding: 4px 12px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  color: #666;
}

.notation-keyboard {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  background: #f9f9f9;
}

.keyboard-row {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 8px;
}

.keyboard-row:last-child {
  margin-bottom: 0;
}

.key-btn {
  width: 48px;
  height: 48px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.key-btn:hover {
  background: #1890ff;
  color: #fff;
  border-color: #1890ff;
}

.key-btn.modifier {
  width: 60px;
  background: #f0f0f0;
}

.image-selector {
  margin-top: 10px;
}

.image-preview {
  position: relative;
  width: 150px;
  height: 150px;
  border: 1px dashed #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  border-radius: 50%;
  font-size: 14px;
  cursor: pointer;
}

.image-options {
  display: flex;
  gap: 15px;
}

.option-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px dashed #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.option-btn .icon {
  font-size: 20px;
}

.file-input {
  display: none;
}

.editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 20px;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 24px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  border: none;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-confirm {
  background: #1890ff;
  color: #fff;
}

.btn-confirm:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.library-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.library-content {
  width: 500px;
  max-height: 600px;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.library-header {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #eee;
}

.library-header h3 {
  margin: 0;
  font-size: 16px;
}

.library-body {
  padding: 15px;
  overflow-y: auto;
  max-height: 500px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.library-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
}

.library-item:hover {
  background: #f5f5f5;
}

.library-item img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}

.library-item span {
  font-size: 12px;
  margin-top: 5px;
  text-align: center;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* === 分类选择器 === */
.category-selector {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.category-selector .form-select {
  flex: 1;
}

.add-category-btn {
  padding: 8px 12px;
  border: 1px dashed #1890ff;
  background: #fff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.add-category-btn:hover {
  background: #e6f7ff;
  border-style: solid;
}

/* === 分类创建弹窗 === */
.category-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
}

.category-dialog {
  width: 450px;
  max-width: 95%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.dialog-header {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #eee;
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.dialog-body {
  padding: 20px;
}

.dialog-body .form-row {
  display: flex;
  gap: 12px;
}

.dialog-body .form-row .form-group {
  flex: 1;
  margin-bottom: 0;
}

.dialog-footer {
  padding: 15px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
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
            <select v-model="form.category" class="form-select">
              <option value="">请选择分类</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
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
import { ref, computed, onMounted, watch } from 'vue'
import ImageCropper from '../ImageCropper.vue'
import { getFormulaCategories, getFormulaList, createFormula, updateFormula } from '@/api/formula'

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

const emit = defineEmits(['close', 'success'])

const fileInput = ref(null)
const form = ref({
  name: '',
  notation: '',
  category: '',
  difficulty: '',
  description: '',
  thumbnail: null
})
const selectedImageUrl = ref('')
const showCropper = ref(false)
const cropperFile = ref(null)
const showLibrary = ref(false)
const categories = ref([])
const libraryFormulas = ref([])

const isEdit = computed(() => !!props.editFormula)

const isValid = computed(() => {
  return form.value.name.trim() && form.value.notation.trim()
})

const topRow = ['R', 'L', 'U', 'D', 'F', 'B']
const middleRow = ['r', 'l', 'u', 'd', 'f', 'b']
const bottomRow = ['M', 'E', 'S', 'x', 'y', 'z']
const modifiers = ["'", '2']

onMounted(async () => {
  await loadCategories()
  await loadLibraryFormulas()
})

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

const loadCategories = async () => {
  try {
    const res = await getFormulaCategories()
    categories.value = res.data
  } catch (e) {
    console.error('加载分类失败', e)
  }
}

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

const clearNotation = () => {
  form.value.notation = ''
}

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    cropperFile.value = file
    showCropper.value = true
  }
}

const handleCrop = (croppedFile) => {
  form.value.thumbnail = croppedFile
  selectedImageUrl.value = URL.createObjectURL(croppedFile)
  showCropper.value = false
}

const removeImage = () => {
  form.value.thumbnail = null
  selectedImageUrl.value = ''
}

const loadLibraryFormulas = async () => {
  try {
    const res = await getFormulaList({ page_size: 100 })
    libraryFormulas.value = res.data?.results || []
  } catch (e) {
    console.error('加载公式库失败', e)
  }
}

const selectFromLibrary = async (formula) => {
  selectedImageUrl.value = formula.thumbnail
  form.value.thumbnail = formula.thumbnail
  showLibrary.value = false
}

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
</style>
<!-- src/components/forum/MarkdownEditor.vue -->
<template>
  <div class="markdown-editor">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <el-button-group>
        <el-button size="small" @click="insertMarkdown('**', '**')" title="粗体">
          <strong>B</strong>
        </el-button>
        <el-button size="small" @click="insertMarkdown('*', '*')" title="斜体">
          <em>I</em>
        </el-button>
        <el-button size="small" @click="insertMarkdown('# ', '')" title="一级标题">H1</el-button>
        <el-button size="small" @click="insertMarkdown('## ', '')" title="二级标题">H2</el-button>
        <el-button size="small" @click="insertMarkdown('### ', '')" title="三级标题">H3</el-button>
        <el-button size="small" @click="insertMarkdown('- ', '')" title="无序列表">列表</el-button>
        <el-button size="small" @click="insertMarkdown('1. ', '')" title="有序列表">1.</el-button>
        <el-button size="small" @click="insertMarkdown('[', '](url)')" title="链接">链接</el-button>
        <el-button size="small" @click="triggerImageUpload" title="上传图片">
            <el-icon><Picture /></el-icon>
            图片
          </el-button>
        <el-button size="small" @click="showFormulaDialog = true" title="插入公式">
            <el-icon><Box /></el-icon>
            公式
          </el-button>
        <el-button size="small" @click="insertMarkdown('```\n', '\n```')" title="代码块">&lt;/&gt;</el-button>
        <el-button size="small" @click="insertMarkdown('> ', '')" title="引用">引用</el-button>
        <el-button size="small" @click="insertMarkdown('---', '')" title="分隔线">—</el-button>
      </el-button-group>

      <div class="toolbar-right">
        <el-upload
          action="#"
          :before-upload="handleFileUpload"
          :show-file-list="false"
          accept=".md"
        >
          <el-button size="small" type="primary">
            <el-icon><Upload /></el-icon>
            上传 .md
          </el-button>
        </el-upload>

        <input
          ref="imageInputRef"
          type="file"
          accept="image/*"
          multiple
          style="display: none;"
          @change="handleImageSelect"
        />

        <el-button size="small" @click="togglePreview">
          <el-icon><View /></el-icon>
          {{ showPreview ? '编辑模式' : '预览模式' }}
        </el-button>
      </div>
    </div>

    <!-- 编辑区（上下布局） -->
    <div class="editor-container">
      <!-- 编辑区 -->
      <div class="editor-pane" v-show="!showPreview">
        <div class="pane-title">
          <span>✏️ 编辑区</span>
          <span class="pane-tip">支持 Markdown 语法</span>
        </div>
        <textarea
          ref="textareaRef"
          v-model="content"
          class="editor-textarea"
          placeholder="使用 Markdown 格式书写...&#10;&#10;支持：标题、列表、代码块、表格、图片、链接等"
        ></textarea>
        <div class="editor-footer">
          <span>字数: {{ content.length }}</span>
          <span>行数: {{ content.split('\n').length }}</span>
        </div>
      </div>

      <!-- 预览区（上下布局时始终显示） -->
      <div class="preview-pane">
        <div class="pane-title">
          <span>👁️ 实时预览</span>
          <el-button
            v-if="showPreview"
            text
            size="small"
            @click="togglePreview"
            style="font-size: 12px;"
          >
            返回编辑
          </el-button>
        </div>
        <div class="preview-content markdown-body" v-html="renderedHtml"></div>
      </div>
    </div>

    <!-- 公式选择弹窗 -->
    <el-dialog
      v-model="showFormulaDialog"
      title="选择魔方公式"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="formula-dialog-content">
        <el-input
          v-model="formulaSearch"
          placeholder="搜索公式名称或记号"
          clearable
          @keyup.enter="loadFormulas"
          @clear="loadFormulas"
          style="margin-bottom: 12px;"
        >
          <template #append>
            <el-button @click="loadFormulas">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>

        <div class="formula-filters">
          <el-select
            v-model="selectedCategory"
            placeholder="选择分类"
            clearable
            style="width: 180px; margin-right: 12px;"
            @change="loadFormulas"
          >
            <el-option
              v-for="cat in formulaCategories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>

          <el-select
            v-model="selectedDifficulty"
            placeholder="选择难度"
            clearable
            style="width: 120px;"
            @change="loadFormulas"
          >
            <el-option label="入门" :value="1" />
            <el-option label="初级" :value="2" />
            <el-option label="中级" :value="3" />
            <el-option label="高级" :value="4" />
            <el-option label="专家" :value="5" />
          </el-select>
        </div>

        <div class="formula-grid" v-loading="formulaLoading">
          <div
            v-for="formula in formulas"
            :key="formula.id"
            class="formula-card"
            @click="selectFormula(formula)"
          >
            <div class="formula-thumbnail" v-if="formula.thumbnail">
              <img :src="formula.thumbnail" :alt="formula.name" />
            </div>
            <div class="formula-thumbnail placeholder" v-else>
              <el-icon><Box /></el-icon>
            </div>
            <div class="formula-info">
              <div class="formula-name">{{ formula.name }}</div>
              <div class="formula-notation">{{ formula.notation }}</div>
              <div class="formula-category">{{ formula.category_name }}</div>
            </div>
          </div>
        </div>

        <el-pagination
          v-model:current-page="formulaPage"
          v-model:page-size="formulaPageSize"
          :total="formulaTotal"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadFormulas"
          @current-change="loadFormulas"
          style="margin-top: 16px; justify-content: center;"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * MarkdownEditor.vue - Markdown 编辑器组件
 * 
 * 核心职责：
 * 1. 提供 Markdown 语法编辑功能（工具栏快捷插入）
 * 2. 实时预览 Markdown 渲染效果
 * 3. 支持代码高亮（highlight.js）
 * 4. 支持图片上传并自动插入 Markdown 格式
 * 5. 支持 .md 文件导入
 * 6. 编辑/预览模式切换
 * 
 * 技术栈：
 * - marked：Markdown 解析库
 * - highlight.js：代码高亮库
 * 
 * 设计要点：
 * - 使用 v-model 双向绑定实现数据同步
 * - 工具栏按钮通过 insertMarkdown 函数插入语法标记
 * - 图片上传成功后自动生成 ![alt](url) 格式
 * - 上下布局：编辑区在上，预览区在下
 */

import { ref, computed, watch, nextTick } from 'vue'
import { Upload, View, Picture, Search, Box } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'           // Markdown 解析库
import hljs from 'highlight.js'           // 代码高亮库
import 'highlight.js/styles/github.css'   // GitHub 风格代码高亮样式
import request from '@/http/request'
import { uploadImage, getFormulasForPost } from '@/api/posts' // 图片上传 API

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const content = ref(props.modelValue)
const textareaRef = ref(null)
const showPreview = ref(false)
const imageInputRef = ref(null)

// 公式选择相关
const showFormulaDialog = ref(false)
const formulaSearch = ref('')
const formulaPage = ref(1)
const formulaPageSize = ref(12)
const formulaTotal = ref(0)
const formulaLoading = ref(false)
const formulas = ref([])
const selectedCategory = ref(null)
const selectedDifficulty = ref(null)
const formulaCategories = ref([])

// 配置 marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true,
  tables: true
})

const renderedHtml = computed(() => {
  if (!content.value) {
    return '<p style="color: #909399;">暂无内容，开始编辑吧...</p>'
  }
  return marked(content.value)
})

watch(content, (newVal) => {
  emit('update:modelValue', newVal)
})

watch(() => props.modelValue, (newVal) => {
  if (newVal !== content.value) {
    content.value = newVal
  }
})

const insertMarkdown = (before, after) => {
  const textarea = textareaRef.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = content.value.substring(start, end)

  const newText = content.value.substring(0, start) +
                  before + selectedText + after +
                  content.value.substring(end)

  content.value = newText

  nextTick(() => {
    textarea.focus()
    const newCursorPos = start + before.length + selectedText.length
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  })
}

const handleFileUpload = (file) => {
  if (!file.name.endsWith('.md')) {
    ElMessage.error('只支持 .md 格式的文件')
    return false
  }

  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 5MB')
    return false
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    content.value = e.target.result
    ElMessage.success('文件上传成功')
  }
  reader.onerror = () => {
    ElMessage.error('文件读取失败')
  }
  reader.readAsText(file)
  return false
}

const togglePreview = () => {
  showPreview.value = !showPreview.value
}

const triggerImageUpload = () => {
  imageInputRef.value?.click()
}

const handleImageSelect = async (event) => {
  const files = Array.from(event.target.files || [])
  if (files.length === 0) return

  const validFiles = files.filter(file => {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if (!validTypes.includes(file.type)) {
      ElMessage.warning(`文件 ${file.name} 不是有效图片格式`)
      return false
    }
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.warning(`文件 ${file.name} 超过 5MB 限制`)
      return false
    }
    return true
  })

  if (validFiles.length === 0) {
    ElMessage.error('没有有效的图片文件')
    return
  }

  const loading = ref(true)
  
  for (let index = 0; index < validFiles.length; index++) {
    const file = validFiles[index]
    try {
      const res = await uploadImage(file)
      if (res.code === 100 && res.image && res.image.image_url) {
        const fileName = file.name.replace(/\.[^/.]+$/, '')
        const imageMarkdown = `![${fileName}](${res.image.image_url})\n`
        
        if (index === 0) {
          insertMarkdown('', imageMarkdown)
        } else {
          content.value += imageMarkdown
        }
      } else {
        ElMessage.error(`图片 ${file.name} 上传失败`)
      }
    } catch (error) {
      console.error('图片上传失败:', error)
      ElMessage.error(`图片 ${file.name} 上传失败`)
    }
  }

  ElMessage.success(`成功添加 ${validFiles.length} 张图片`)
  event.target.value = ''
}

// 公式选择相关方法
const loadFormulas = async () => {
  formulaLoading.value = true
  try {
    const params = {
      page: formulaPage.value,
      page_size: formulaPageSize.value,
      search: formulaSearch.value || undefined,
      category: selectedCategory.value || undefined,
      difficulty: selectedDifficulty.value || undefined
    }
    const res = await getFormulasForPost(params)
    if (res.code === 100) {
      formulas.value = res.data.results || []
      formulaTotal.value = res.data.count || 0
    }
  } catch (error) {
    console.error('加载公式失败:', error)
    ElMessage.error('加载公式失败')
  } finally {
    formulaLoading.value = false
  }
}

const loadFormulaCategories = async () => {
  try {
    const res = await request({
      url: '/api/formula/categories/',
      method: 'get'
    })
    if (res.code === 100) {
      formulaCategories.value = res.data.map(cat => ({
        id: cat.id,
        name: `${cat.order}阶 ${cat.method} ${cat.phase}`
      }))
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const selectFormula = (formula) => {
  if (!formula.thumbnail) {
    ElMessage.warning('该公式没有缩略图，无法插入')
    return
  }

  const imageMarkdown = `![${formula.name}](${formula.thumbnail})\n`
  insertMarkdown('', imageMarkdown)
  showFormulaDialog.value = false
  ElMessage.success(`已插入公式：${formula.name}`)
}

watch(showFormulaDialog, (newVal) => {
  if (newVal) {
    formulaPage.value = 1
    loadFormulaCategories()
    loadFormulas()
  }
})
</script>

<style scoped>
.markdown-editor {
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.editor-toolbar {
  padding: 8px 12px;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f7fa;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 上下布局 */
.editor-container {
  display: flex;
  flex-direction: column;
  height: 1080px;
}

.editor-pane, .preview-pane {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 500px;
  overflow: hidden;
}

.editor-pane {
  border-bottom: 1px solid #dcdfe6;
}

.pane-title {
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #dcdfe6;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pane-tip {
  font-size: 11px;
  color: #909399;
  font-weight: normal;
}

.editor-textarea {
  flex: 1;
  width: 100%;
  border: none;
  padding: 12px;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  outline: none;
  background: #fff;
}

.editor-textarea:focus {
  background: #fefce8;
}

.editor-footer {
  padding: 6px 12px;
  border-top: 1px solid #dcdfe6;
  background: #fafafa;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fff;
}

/* 预览模式：只显示预览区 */
.editor-container.preview-mode .editor-pane {
  display: none;
}

.editor-container.preview-mode .preview-pane {
  flex: 1;
}

/* 响应式 */
@media (max-width: 768px) {
  .editor-container {
    height: 500px;
  }

  .editor-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-right {
    justify-content: flex-end;
  }
}

/* 公式选择弹窗样式 */
.formula-dialog-content {
  max-height: 550px;
  overflow-y: auto;
}

.formula-filters {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.formula-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.formula-card {
  cursor: pointer;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 10px;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.formula-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  transform: translateY(-2px);
}

.formula-thumbnail {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 6px;
  background: #f5f7fa;
}

.formula-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.formula-thumbnail.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.formula-thumbnail.placeholder .el-icon {
  font-size: 32px;
}

.formula-info {
  width: 100%;
}

.formula-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.formula-notation {
  font-size: 11px;
  color: #409eff;
  margin-bottom: 4px;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.formula-category {
  font-size: 10px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
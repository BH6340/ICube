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
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Upload, View, Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import { uploadImage } from '@/api/posts'

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
</style>
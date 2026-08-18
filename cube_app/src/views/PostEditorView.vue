<script setup>
/**
 * PostEditorView.vue — 帖子编辑器（创建/编辑）
 * 简化 Markdown 编辑：纯文本 + 图片插入 + 标签选择
 * 存储格式统一为 Markdown，与 Web 端完全兼容
 */
defineOptions({ name: 'PostEditorView' })

import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { marked } from 'marked'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'
import { createPost, updatePost, getPost, getTags, uploadPostImage } from '@/api/forum'
import { buildMediaUrl } from '@/utils/media-url'

const router = useRouter()
const route = useRoute()

const isEdit = computed(() => !!route.params.id)
const title = ref('')
const content = ref('')
const tagIds = ref([])
const tags = ref([])
const submitting = ref(false)
const imageUploading = ref(false)
const previewMode = ref(false)
const textareaRef = ref()

marked.setOptions({ breaks: true, gfm: true })

const previewHtml = computed(() => {
  if (!content.value) return '<p style="color:#999">预览区为空</p>'
  const processedMd = content.value.replace(
    /!\[([^\]]*)\]\(([^)]+)\)/g,
    (match, alt, url) => {
      if (url.startsWith('http')) return match
      return `![${alt}](${buildMediaUrl(url)})`
    }
  )
  return marked.parse(processedMd)
})

onMounted(async () => {
  try {
    const res = await getTags()
    tags.value = res.data?.results || res.data || []
  } catch {}

  if (isEdit.value) {
    try {
      const res = await getPost(route.params.id)
      const post = res.data?.post || res.data || res
      title.value = post.title || ''
      content.value = post.content_md || post.content || ''
      tagIds.value = (post.tags || []).map(t => typeof t === 'object' ? t.id : t)
    } catch {
      showToast('加载帖子失败')
    }
  }
})

function toggleTag(tagId) {
  const idx = tagIds.value.indexOf(tagId)
  if (idx > -1) {
    tagIds.value.splice(idx, 1)
  } else {
    tagIds.value.push(tagId)
  }
}

const showImageSheet = ref(false)
const imageActions = [
  { name: '拍照', action: 'camera' },
  { name: '从相册选择', action: 'gallery' },
]

function onImageAction(item) {
  showImageSheet.value = false
  insertImage(item.action)
}

async function insertImage(source) {
  try {
    const photo = await Camera.getPhoto({
      resultType: CameraResultType.DataUrl,
      source: source === 'camera' ? CameraSource.Camera : CameraSource.Photos,
      quality: 80,
    })

    imageUploading.value = true
    const fetchRes = await fetch(photo.dataUrl)
    const blob = await fetchRes.blob()
    const file = new File([blob], `image.${photo.format || 'jpg'}`, { type: blob.type })

    const uploadRes = await uploadPostImage(file)
    const imageUrl = uploadRes.image?.image_url
    if (!imageUrl) throw new Error('上传失败')

    const md = `![图片](${imageUrl})\n`
    const textarea = textareaRef.value
    if (textarea) {
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      content.value = content.value.substring(0, start) + md + content.value.substring(end)
      nextTick(() => {
        textarea.focus()
        const pos = start + md.length
        textarea.setSelectionRange(pos, pos)
      })
    } else {
      content.value += md
    }
    showToast({ type: 'success', message: '图片已插入' })
  } catch (e) {
    if (e.message !== 'User cancelled photos app') {
      showToast('图片上传失败')
    }
  } finally {
    imageUploading.value = false
  }
}

function insertText(prefix, suffix = '') {
  const textarea = textareaRef.value
  if (!textarea) {
    content.value += prefix + suffix
    return
  }
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selected = content.value.substring(start, end)
  const newText = prefix + selected + suffix
  content.value = content.value.substring(0, start) + newText + content.value.substring(end)
  nextTick(() => {
    textarea.focus()
    const pos = start + newText.length
    textarea.setSelectionRange(pos, pos)
  })
}

async function submit() {
  if (!title.value.trim()) {
    showToast('请输入标题')
    return
  }
  if (title.value.trim().length < 3) {
    showToast('标题至少 3 个字符')
    return
  }
  if (!content.value.trim()) {
    showToast('请输入内容')
    return
  }

  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('title', title.value.trim())
    formData.append('content', content.value)
    formData.append('content_md', content.value)
    tagIds.value.forEach(id => formData.append('tag_ids', id))

    if (isEdit.value) {
      await updatePost(route.params.id, formData)
      showToast({ type: 'success', message: '更新成功' })
    } else {
      await createPost(formData)
      showToast({ type: 'success', message: '发布成功' })
    }
    router.replace('/forum')
  } catch {
    // request.js 已处理错误提示
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page">
    <van-nav-bar
      :title="isEdit ? '编辑帖子' : '发帖'"
      left-arrow
      @click-left="router.back()"
      placeholder
    >
      <template #right>
        <van-button size="small" type="primary" :loading="submitting" @click="submit">
          发布
        </van-button>
      </template>
    </van-nav-bar>

    <div class="editor-content">
      <van-field
        v-model="title"
        placeholder="请输入标题（3-200字符）"
        maxlength="200"
        show-word-limit
        class="title-field"
      />

      <div class="tag-section">
        <div class="tag-label">标签</div>
        <div class="tag-chips">
          <span
            v-for="tag in tags"
            :key="tag.id"
            class="tag-chip"
            :class="{ active: tagIds.includes(tag.id) }"
            @click="toggleTag(tag.id)"
          >
            {{ tag.name }}
          </span>
          <span v-if="tags.length === 0" class="no-tags">暂无标签</span>
        </div>
      </div>

      <div class="toolbar">
        <button class="tool-btn" @click="showImageSheet = true">
          <van-icon name="photo-o" size="20" />
        </button>
        <button class="tool-btn" @click="insertText('**', '**')">
          <span class="tool-text">B</span>
        </button>
        <button class="tool-btn" @click="insertText('## ')">
          <span class="tool-text">H</span>
        </button>
        <button class="tool-btn" @click="insertText('- ')">
          <span class="tool-text">列表</span>
        </button>
        <button class="tool-btn" @click="insertText('[', '](url)')">
          <van-icon name="link-o" size="20" />
        </button>
        <div class="toolbar-spacer" />
        <van-button
          size="mini"
          :type="previewMode ? 'primary' : 'default'"
          @click="previewMode = !previewMode"
        >
          {{ previewMode ? '编辑' : '预览' }}
        </van-button>
      </div>

      <div class="editor-area">
        <van-loading v-if="imageUploading" class="upload-loading">图片上传中...</van-loading>

        <textarea
          v-if="!previewMode"
          ref="textareaRef"
          v-model="content"
          class="content-textarea"
          placeholder="请输入帖子内容..."
        />
        <div v-else class="markdown-body" v-html="previewHtml"></div>
      </div>
    </div>

    <van-action-sheet
      v-model:show="showImageSheet"
      :actions="imageActions"
      @select="onImageAction"
      cancel-text="取消"
      close-on-click-action
    />
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.title-field {
  padding: 12px 16px;
}

.title-field :deep(.van-field__control) {
  font-size: 1.05rem;
  font-weight: 600;
}

.tag-section {
  padding: 8px 16px 12px;
  border-bottom: 1px solid var(--van-border-color);
}

.tag-label {
  font-size: 0.85rem;
  color: var(--van-text-color-2);
  margin-bottom: 8px;
}

.tag-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  padding: 4px 12px;
  font-size: 0.82rem;
  border-radius: 12px;
  background: var(--van-background);
  color: var(--van-text-color-2);
  border: 1px solid var(--van-border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.tag-chip.active {
  background: var(--van-primary-color);
  color: #fff;
  border-color: var(--van-primary-color);
}

.no-tags {
  font-size: 0.8rem;
  color: var(--van-text-color-3);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--van-border-color);
  background: var(--van-background-2);
}

.tool-btn {
  border: none;
  background: transparent;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  min-height: 32px;
  transition: background 0.15s;
}

.tool-btn:active {
  background: var(--van-background);
}

.tool-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--van-text-color);
}

.toolbar-spacer {
  flex: 1;
}

.editor-area {
  flex: 1;
  overflow-y: auto;
  position: relative;
  -webkit-overflow-scrolling: touch;
}

.upload-loading {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.content-textarea {
  width: 100%;
  min-height: 100%;
  border: none;
  padding: 16px;
  font-size: 0.92rem;
  line-height: 1.7;
  resize: none;
  outline: none;
  font-family: inherit;
  background: transparent;
}
</style>

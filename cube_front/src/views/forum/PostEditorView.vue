<!-- src/views/forum/PostEditorView.vue -->
<template>
  <div class="post-editor-container">
    <el-card class="editor-card" shadow="never">
      <template #header>
        <div class="card-header">
          <h2>{{ isEdit ? '编辑帖子' : '发布新帖子' }}</h2>
          <div class="header-actions">
            <el-button v-if="isEdit" type="info" link @click="goBack">
              <el-icon>
                <Back/>
              </el-icon>
              返回
            </el-button>
          </div>
        </div>
      </template>

      <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="80px"
          label-position="top"
      >
        <!-- 标题 -->
        <el-form-item label="标题" prop="title">
          <el-input
              v-model="form.title"
              placeholder="请输入标题（至少5个字符，最多200个字符）"
              maxlength="200"
              show-word-limit
              clearable
              size="large"
          />
        </el-form-item>

        <!-- 标签 -->
        <el-form-item label="标签" prop="tag_ids">
          <TagSelector v-model="form.tag_ids"/>
        </el-form-item>

        <!-- 内容 -->
        <el-form-item label="内容" prop="content">
          <div class="content-tip">
            <el-icon>
              <InfoFilled/>
            </el-icon>
            支持 Markdown 格式，可上传 .md 文件
          </div>
          <!-- 包裹一层容器，打破 el-form-item 默认的 Flex 限制，防止提示横向并列 -->
          <div style="width: 100%;">
            <MarkdownEditor v-model="form.content"/>
          </div>
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <div class="form-actions">
            <el-button type="primary" @click="handleSubmit" :loading="submitting" size="large">
              <el-icon>
                <Promotion/>
              </el-icon>
              {{ isEdit ? '保存修改' : '发布帖子' }}
            </el-button>
            <el-button @click="goBack" size="large">
              <el-icon>
                <Close/>
              </el-icon>
              取消
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
/**
 * PostEditorView.vue - 帖子编辑器视图
 *
 * 核心职责：
 * 1. 提供帖子创建/编辑的表单界面
 * 2. 集成 MarkdownEditor 组件实现富文本编辑
 * 3. 集成 TagSelector 组件实现标签选择
 * 4. 表单校验与提交逻辑
 *
 * 功能特性：
 *   - 标题最少 5 字符，最多 200 字符
 *   - 内容最少 10 字符，支持 Markdown 格式
 *   - 标签支持多选
 *   - 编辑模式自动加载已有数据
 *
 * 设计要点：
 *   - 创建和编辑共用同一组件，通过路由参数区分模式
 *   - 提交时使用 FormData 格式，支持文件上传扩展
 *   - 响应式设计：移动端表单操作区纵向排列
 */

import {ref, reactive, computed, onMounted} from 'vue'
import {useRouter, useRoute} from 'vue-router'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Back, Promotion, Close, InfoFilled} from '@element-plus/icons-vue'
import {getPost, createPost, updatePost} from '@/api/posts'
import MarkdownEditor from '@/components/forum/MarkdownEditor.vue'
import TagSelector from '@/components/forum/TagSelector.vue'

const router = useRouter()
const route = useRoute()

/** 表单引用 */
const formRef = ref(null)
/** 提交状态 */
const submitting = ref(false)

/** 是否为编辑模式（通过路由参数判断） */
const isEdit = computed(() => !!route.params.id)

/** 表单数据 */
const form = reactive({
  title: '',       // 帖子标题
  content: '',     // Markdown 内容
  tag_ids: []      // 标签 ID 列表
})

/** 表单校验规则 */
const rules = {
  title: [
    {required: true, message: '请输入标题', trigger: 'blur'},
    {min: 5, message: '标题至少5个字符', trigger: 'blur'},
    {max: 200, message: '标题不能超过200个字符', trigger: 'blur'}
  ],
  content: [
    {required: true, message: '请输入内容', trigger: 'blur'},
    {min: 10, message: '内容至少10个字符', trigger: 'blur'}
  ]
}

/**
 * 加载帖子数据（编辑模式）
 *
 * 根据路由参数获取帖子 ID，加载已有数据填充表单。
 * 提取逻辑兼容后端不同响应格式（res.post / res.data.post）。
 */
const loadPost = async () => {
  const id = route.params.id
  if (!id) return

  try {
    const res = await getPost(id)

    let postData = null
    if (res.code === 100) {
      postData = res.post
    } else if (res.code === 0) {
      postData = res.data?.post
    } else if (res.post) {
      postData = res.post
    }

    if (postData) {
      form.title = postData.title || ''
      form.content = postData.content || postData.content_md || ''
      if (postData.tags && postData.tags.length > 0) {
        form.tag_ids = postData.tags.map(tag => Number(tag.id))
      } else {
        form.tag_ids = []
      }
    } else {
      ElMessage.error('加载帖子失败')
      router.push('/forum')
    }
  } catch (error) {
    console.error('加载帖子失败:', error)
    ElMessage.error('加载帖子失败')
    router.push('/forum')
  }
}

/**
 * 提交表单
 *
 * 校验通过后，根据模式调用创建或更新接口。
 * 使用 FormData 格式便于扩展文件上传。
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请完整填写表单')
    return
  }

  if (isEdit.value) {
    try {
      await ElMessageBox.confirm('确定要保存修改吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      })
    } catch {
      return
    }
  }

  submitting.value = true

  try {
    const formData = new FormData()
    formData.append('title', form.title.trim())
    formData.append('content', form.content)

    if (form.tag_ids && form.tag_ids.length) {
      form.tag_ids.forEach(id => {
        formData.append('tag_ids', id)
      })
    }

    let result
    if (isEdit.value) {
      result = await updatePost(route.params.id, formData)
    } else {
      result = await createPost(formData)
    }

    console.log('提交响应:', result)

    let postId = null
    if (result.code === 100 || result.code === 0) {
      postId = result.post?.id || result.data?.post?.id
      if (postId) {
        ElMessage.success(isEdit.value ? '保存成功' : '发布成功')
        router.push(`/forum/post/${postId}`)
      } else {
        ElMessage.error('操作成功但无法获取帖子ID')
      }
    } else {
      ElMessage.error(result.msg || (isEdit.value ? '保存失败' : '发布失败'))
    }
  } catch (error) {
    console.error('提交失败', error)
    ElMessage.error(isEdit.value ? '保存失败，请重试' : '发布失败，请重试')
  } finally {
    submitting.value = false
  }
}

/** 返回上一页 */
const goBack = () => {
  router.back()
}

onMounted(() => {
  if (isEdit.value) {
    document.title = '编辑帖子 - 魔方论坛'
    loadPost()
  } else {
    document.title = '发布新帖子 - 魔方论坛'
  }
})
</script>

<style scoped>
.post-editor-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.editor-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 22px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}

/* 内容提示样式 - 独立显示在编辑框下方 */
.content-tip {
  font-size: 12px;
  color: #67c23a;
  margin-top: 8px;
  padding: 6px 12px;
  background: #f0f9eb;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  clear: both;
  /* 修复核心：强制独占一行，摆脱父级 flex 并列干扰 */
  width: 100%;
  box-sizing: border-box;
}

.content-tip .el-icon {
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  margin-top: 20px;
}

.form-actions .el-button {
  min-width: 120px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .post-editor-container {
    padding: 12px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .form-actions {
    flex-direction: column;
  }

  .form-actions .el-button {
    width: 100%;
  }

  .content-tip {
    font-size: 11px;
    padding: 4px 10px;
  }
}
</style>
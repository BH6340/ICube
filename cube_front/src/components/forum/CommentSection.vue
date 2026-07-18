<template>
  <div class="comment-section">
    <div class="comment-form" v-if="isLoggedIn">
      <el-avatar :size="32" :src="userAvatar || defaultAvatar"/>
      <div class="form-content">
        <el-input
            v-model="newComment"
            type="textarea"
            :rows="3"
            placeholder="写下你的评论..."
            maxlength="500"
            show-word-limit
        />
        <div class="form-actions">
          <el-button type="primary" @click="submitComment" :loading="submitting" size="default">
            发表评论
          </el-button>
        </div>
      </div>
    </div>

    <div v-else class="login-tip">
      <el-alert title="请先登录后再发表评论" type="info" :closable="false" show-icon/>
    </div>

    <div class="comments-list" v-loading="loading">
      <div v-if="!comments || comments.length === 0" class="empty-comments">
        <el-empty description="暂无评论，快来抢沙发吧！" :image-size="80"/>
      </div>

      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-main">
          <el-avatar :size="36" :src="comment.author?.image || defaultAvatar" class="comment-avatar"/>
          <div class="comment-content">
            <div class="comment-header">
              <span class="author-name">{{ comment.author?.username }}</span>
              <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            </div>
            <div class="comment-body">{{ comment.content }}</div>
            <div class="comment-actions">
              <el-button
                  text
                  size="small"
                  :type="comment.liked ? 'primary' : 'info'"
                  @click="clickLike(comment)"
                  :disabled="comment._reactionLoading"
                  class="action-btn"
              >
                <span v-if="comment.liked">👍</span>
                <span v-else>👍🏻</span>
                <span class="count-num">{{ comment.like_count || 0 }}</span>
              </el-button>

              <el-button
                  text
                  size="small"
                  :type="comment.disliked ? 'danger' : 'info'"
                  @click="clickDislike(comment)"
                  :disabled="comment._reactionLoading"
                  class="action-btn"
              >
                <span v-if="comment.disliked">👎</span>
                <span v-else>👎🏻</span>
                <span class="count-num">{{ comment.dislike_count || 0 }}</span>
              </el-button>
              <el-button text size="small" @click="replyTo(comment)">
                💬 回复
              </el-button>
              <el-button
                  v-if="comment.author?.username === currentUsername || isAdmin"
                  text
                  size="small"
                  type="danger"
                  @click="handleDelete(comment)"
              >
                🗑️ 删除
              </el-button>
            </div>

            <div class="reply-form" v-if="replyTarget === comment.id">
              <el-input
                  v-model="replyContent"
                  type="textarea"
                  :rows="2"
                  :placeholder="`回复 @${comment.author?.username}`"
                  maxlength="500"
              />
              <div class="reply-actions">
                <el-button size="small" @click="cancelReply">取消</el-button>
                <el-button size="small" type="primary" @click="submitReply" :loading="replySubmitting">
                  回复
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="replies-list" v-if="comment.replies && comment.replies.length">
          <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
            <div class="reply-main">
              <el-avatar :size="28" :src="reply.author?.image || defaultAvatar" class="reply-avatar"/>
              <div class="reply-content">
                <div class="reply-header">
                  <span class="author-name">{{ reply.author?.username }}</span>
                  <span v-if="reply.parent" class="reply-to">
                    回复 @{{ getReplyToUsername(reply) }}
                  </span>
                  <span class="reply-time">{{ formatTime(reply.created_at) }}</span>
                </div>
                <div class="reply-body">{{ reply.content }}</div>
                <div class="reply-actions">
                  <el-button
                      text
                      size="small"
                      :type="reply.liked ? 'primary' : 'info'"
                      @click="clickLike(reply)"
                      :disabled="reply._reactionLoading"
                  >
                    <span v-if="reply.liked">👍</span>
                    <span v-else>👍🏻</span>
                    <span class="count-num">{{ reply.like_count || 0 }}</span>
                  </el-button>

                  <el-button
                      text
                      size="small"
                      :type="reply.disliked ? 'danger' : 'info'"
                      @click="clickDislike(reply)"
                      :disabled="reply._reactionLoading"
                  >
                    <span v-if="reply.disliked">👎</span>
                    <span v-else>👎🏻</span>
                    <span class="count-num">{{ reply.dislike_count || 0 }}</span>
                  </el-button>
                  <el-button text size="small" @click="replyToReply(reply)">
                    💬 回复
                  </el-button>
                  <el-button
                      v-if="reply.author?.username === currentUsername || isAdmin"
                      text
                      size="small"
                      type="danger"
                      @click="handleDelete(reply)"
                  >
                    🗑️ 删除
                  </el-button>
                </div>

                <div class="reply-form" v-if="replyTarget === reply.id">
                  <el-input
                      v-model="replyContent"
                      type="textarea"
                      :rows="2"
                      :placeholder="`回复 @${reply.author?.username}`"
                      maxlength="500"
                  />
                  <div class="reply-actions">
                    <el-button size="small" @click="cancelReply">取消</el-button>
                    <el-button size="small" type="primary" @click="submitReply" :loading="replySubmitting">
                      回复
                    </el-button>
                  </div>
                </div>

              </div>
            </div>
          </div>

          <div v-if="comment.reply_count > 3 && comment.replies.length === 3" class="load-more-replies">
            <el-button text @click="loadMoreReplies(comment)">
              <el-icon>
                <More/>
              </el-icon>
              展开更多回复 ({{ comment.reply_count - 3 }})
            </el-button>
          </div>
        </div>
      </div>

      <div class="pagination" v-if="total > pageSize">
        <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="loadComments"
            small
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {CaretBottom, CaretTop, More} from '@element-plus/icons-vue'
import {
  getComments,
  createComment,
  deleteComment,
  likeComment as apiLikeComment,
  dislikeComment as apiDislikeComment
} from '@/api/comments'
import defaultAvatar from '@/assets/default_avatar.svg'

const props = defineProps({
  postId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['comment-added', 'comment-count-updated'])

const comments = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const submitting = ref(false)
const replySubmitting = ref(false)

const newComment = ref('')
const replyContent = ref('')
const replyTarget = ref(null)
const replyToComment = ref(null)

const isLoggedIn = computed(() => !!localStorage.getItem('token'))
const currentUsername = computed(() => localStorage.getItem('username') || '')
const userAvatar = computed(() => localStorage.getItem('image') || '')
const isAdmin = computed(() => false)

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return `${minutes}分钟前`
    }
    return `${hours}小时前`
  } else if (days < 7) {
    return `${days}天前`
  }
  return date.toLocaleDateString()
}

// 💡 标注修改：修复“自己回复自己”的显示问题
// 建立一个全称映射表，用来缓存用户名以便多级查询
const replyUserMap = ref({})

const getReplyToUsername = (reply) => {
  // 如果后端返回了 parent 对象的详细数据或被回复者属性，直接返回它
  if (reply.reply_to_name) return reply.reply_to_name
  if (reply.parent_author?.username) return reply.parent_author.username

  // 备用兜底方案：从缓存的映射表中，根据依赖的父级评论 ID 动态找人名
  const parentId = reply.parent_id || reply.parent
  if (parentId && replyUserMap.value[parentId]) {
    return replyUserMap.value[parentId]
  }
  return '用户'
}

// 💡 标注修改：核心黑科技！递归打平深层子回复的算法
// 这个函数会将三级、四级等深度嵌套的数据递归抽取到一个扁平的数组中，并记录父子称呼依赖
const flattenReplies = (replyList, parentUsername = '') => {
  let result = []
  if (!replyList || replyList.length === 0) return result

  replyList.forEach(reply => {
    // 缓存当前评论的用户，供深层追查使用
    if (reply.id && reply.author?.username) {
      replyUserMap.value[reply.id] = reply.author.username
    }

    // 如果上级是二级，记录谁是谁回复的
    if (parentUsername) {
      reply.reply_to_name = parentUsername
    }

    // 存入当前层级的数据
    result.push(reply)

    // 💡 关键：如果这个回复里还藏有更深一层的 replies 嵌套，递归抽取它
    if (reply.replies && reply.replies.length > 0) {
      const subFlatted = flattenReplies(reply.replies, reply.author?.username)
      result = result.concat(subFlatted)
    }
  })
  return result
}

const loadComments = async () => {
  loading.value = true
  try {
    const res = await getComments(props.postId, {
      page: currentPage.value,
      page_size: pageSize.value
    })

    if (res.code === 100) {
      const rawComments = res.data?.results || []

      // 💡 标注修改：在赋值给页面渲染前，清洗并扁平化子级链条
      replyUserMap.value = {} // 重置缓存
      comments.value = rawComments.map(comment => {
        // 先把一级主评论的作者丢进缓存
        if (comment.id && comment.author?.username) {
          replyUserMap.value[comment.id] = comment.author.username
        }

        // 递归打平这个主评论下的所有子代回复
        if (comment.replies && comment.replies.length > 0) {
          comment.replies = flattenReplies(comment.replies)
          // 按照时间由远及近正序排列
          comment.replies.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
        }
        return comment
      })

      total.value = res.data?.count || 0
    } else {
      comments.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('加载评论失败:', error)
    comments.value = []
    total.value = 0
    ElMessage.error('加载评论失败')
  } finally {
    loading.value = false
  }
}

const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }

  submitting.value = true
  try {
    const res = await createComment({
      post: props.postId,
      content: newComment.value
    })
    if (res.code === 100) {
      ElMessage.success('评论成功')
      newComment.value = ''
      await loadComments()
      emit('comment-added')
      emit('comment-count-updated')
    }
  } catch (error) {
    ElMessage.error('评论失败')
  } finally {
    submitting.value = false
  }
}

// 💡 标注修改：修改了传递参数，使其更加健壮
const submitReply = async () => {
  if (!replyContent.value.trim() || !replyToComment.value) {
    ElMessage.warning('请输入回复内容')
    return
  }

  replySubmitting.value = true
  try {
    // 锁死真实的父评论 ID
    const parentId = replyToComment.value.id

    const res = await createComment({
      post: props.postId,
      parent: parentId,
      content: replyContent.value
    })

    if (res.code === 100) {
      ElMessage.success('回复成功')
      replyContent.value = ''
      replyTarget.value = null
      replyToComment.value = null
      await loadComments()
      emit('comment-added')
      emit('comment-count-updated')
    }
  } catch (error) {
    ElMessage.error('回复失败')
  } finally {
    replySubmitting.value = false
  }
}

const replyTo = (comment) => {
  replyTarget.value = comment.id
  replyToComment.value = comment
  replyContent.value = ''
}

// 💡 标注修改：让输入框直接贴在被点击的二级评论自己的 id 下方，增强现场交互感
const replyToReply = (reply) => {
  replyTarget.value = reply.id
  replyToComment.value = reply
  replyContent.value = ''
}

const cancelReply = () => {
  replyTarget.value = null
  replyToComment.value = null
  replyContent.value = ''
}

const handleCommentReaction = async (comment, isLike) => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再操作')
    return
  }

  if (comment._reactionLoading) return
  comment._reactionLoading = true

  try {
    const apiCall = isLike ? apiLikeComment : apiDislikeComment
    const res = await apiCall(comment.id)

    if (res.code === 100) {
      comment.like_count = res.data.like_count
      comment.dislike_count = res.data.dislike_count
      comment.liked = res.data.liked
      comment.disliked = res.data.disliked

      if (res.data.reaction === 'none') {
        ElMessage.success('已取消操作')
      } else {
        ElMessage.success(isLike ? '点赞成功' : '点踩成功')
      }
    }
  } catch (error) {
    console.error('评价评论失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    setTimeout(() => {
      comment._reactionLoading = false
    }, 300)
  }
}

const clickLike = (comment) => handleCommentReaction(comment, true)
const clickDislike = (comment) => handleCommentReaction(comment, false)

const handleDelete = async (comment) => {
  ElMessageBox.confirm('确定要删除这条评论吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteComment(comment.id)
      if (res.code === 100) {
        ElMessage.success('删除成功')
        await loadComments()
        emit('comment-count-updated')
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {
  })
}

const loadMoreReplies = async (comment) => {
  await loadComments()
}

onMounted(() => {
  loadComments()
})
</script>

<style scoped>
/* 保持你的原有样式，未做任何删减变动 */
.comment-section {
  margin-top: 20px;
}
.comment-form {
  display: flex;
  gap: 16px;
  margin-bottom: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 12px;
}
.form-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.form-actions {
  margin-top: 16px;
  text-align: right;
}
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.comment-item {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 20px;
}
.comment-main {
  display: flex;
  gap: 12px;
}
.comment-avatar {
  flex-shrink: 0;
}
.comment-content {
  flex: 1;
}
.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.author-name {
  font-weight: 500;
  color: #409eff;
}
.comment-time {
  font-size: 12px;
  color: #909399;
}
.comment-body {
  line-height: 1.6;
  color: #303133;
  margin-bottom: 10px;
  word-break: break-word;
}
.comment-actions {
  display: flex;
  gap: 16px;
}
.replies-list {
  margin-top: 16px;
  margin-left: 36px;
  padding-left: 16px;
  border-left: 2px solid #e4e7ed;
}
.reply-item {
  margin-bottom: 16px;
}
.reply-main {
  display: flex;
  gap: 10px;
}
.reply-avatar {
  flex-shrink: 0;
}
.reply-content {
  flex: 1;
}
.reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.reply-to {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}
.reply-time {
  font-size: 11px;
  color: #909399;
}
.reply-body {
  font-size: 13px;
  line-height: 1.5;
  color: #606266;
  margin-bottom: 8px;
  word-break: break-word;
}
.reply-actions {
  display: flex;
  gap: 12px;
}
.reply-form {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}
.reply-actions {
  margin-top: 8px;
  text-align: right;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
.login-tip {
  margin-bottom: 20px;
}
.empty-comments {
  padding: 40px 0;
}
.load-more-replies {
  margin-top: 8px;
  text-align: center;
}
</style>
<template>
  <div class="formula-library">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="8" :md="6">
        <div class="sidebar">
          <el-card shadow="never" class="category-card">
            <template #header>
              <span>公式分类</span>
            </template>
            <el-tree :data="categoryTree" :props="{ label: 'name', children: 'children' }" :expand-on-click-node="false"
              :highlight-current="true" @node-click="handleCategoryClick" default-expand-all />
          </el-card>

          <el-card shadow="never" class="filter-card">
            <template #header>
              <span>难度筛选</span>
            </template>
            <el-checkbox-group v-model="selectedDifficulties" @change="handleFilterChange">
              <el-checkbox label="基础" border>基础</el-checkbox>
              <el-checkbox label="进阶" border>进阶</el-checkbox>
              <el-checkbox label="困难" border>困难</el-checkbox>
            </el-checkbox-group>
          </el-card>

          <el-card shadow="never" class="search-card">
            <template #header>
              <span>搜索公式</span>
            </template>
            <el-input v-model="searchKeyword" placeholder="输入公式名称或记号" prefix-icon="Search" clearable
              @keyup.enter="handleSearch" @clear="handleSearch" @input="handleSearch" />
          </el-card>
        </div>
      </el-col>

      <el-col :xs="24" :sm="16" :md="18">
        <div class="main-content">
          <div class="toolbar">
            <div class="toolbar-left">
              <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="toolbar-tabs">
                <el-tab-pane label="我的收藏" name="collections">
                  <span class="result-count">共 {{ total }} 个收藏公式</span>
                </el-tab-pane>
                <el-tab-pane label="我的公式" name="my_formulas">
                  <span class="result-count">共 {{ total }} 个自创公式</span>
                </el-tab-pane>
              </el-tabs>
            </div>
            <div class="toolbar-right">
              <el-button
                  v-if="activeTab === 'my_formulas'"
                  type="primary"
                  size="small"
                  @click="handleAddFormula"
                  icon="Plus"
              >
                添加新公式
              </el-button>
              <el-select v-model="sortBy" @change="handleSortChange" style="width: 120px; margin-left: 10px">
                <el-option label="默认排序" value="default" />
                <el-option label="难度升序" value="difficulty_asc" />
                <el-option label="难度降序" value="difficulty_desc" />
              </el-select>
            </div>
          </div>

          <div class="formula-grid">
            <el-card v-for="formula in formulaList" :key="formula.id" class="formula-card"
              @click="handleFormulaClick(formula)" hover>
              <div class="formula-header">
                <span class="formula-name">{{ formula.name }}</span>
                <el-tag :type="difficultyTagType(formula.difficulty)" size="small">
                  {{ difficultyLabel(formula.difficulty) }}
                </el-tag>
              </div>
              <div class="formula-notation">{{ formula.notation }}</div>
              <div v-if="formula.thumbnail" class="formula-thumbnail">
                <img :src="formula.thumbnail" :alt="formula.name" />
              </div>
              <div v-else class="formula-thumbnail placeholder">
                <el-icon size="48" color="#ccc">
                  <Picture />
                </el-icon>
              </div>
              <div class="formula-footer">
                <div class="footer-left">
                  <span class="category-tag">{{ formula.category?.name }}</span>
                  <span v-if="formula.author" class="author-tag">{{ formula.author.username }}</span>
                </div>
                <div class="footer-right">
                  <el-button
                      v-if="activeTab === 'my_formulas'"
                      type="primary"
                      size="small"
                      @click.stop="handleEditFormula(formula)"
                      icon="Edit"
                  >
                    编辑
                  </el-button>
                  <el-button
                      v-if="activeTab === 'collections'"
                      type="text"
                      size="small"
                      @click.stop="removeCollectionItem(formula)"
                      class="collected"
                  >
                    <el-icon><Star /></el-icon>
                    取消收藏
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>

          <div v-if="total > pageSize" class="pagination-wrapper">
            <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total"
              layout="total, prev, pager, next" @current-change="handlePageChange" />
          </div>

          <div v-if="total === 0" class="empty-state">
            <el-empty description="暂无收藏的公式" :image-size="120">
              <el-button type="primary" @click="$router.push('/formulas')">去收藏公式</el-button>
            </el-empty>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="showDetailDialog" :title="selectedFormula?.name" width="900px">
      <div v-if="selectedFormula" class="formula-detail">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="8">
            <div class="detail-info compact">
              <div class="detail-item">
                <span class="label">公式记号：</span>
                <code class="notation">{{ selectedFormula.notation }}</code>
              </div>
              <div class="detail-item">
                <span class="label">逆公式：</span>
                <code class="notation">{{ selectedFormula.inverse_notation }}</code>
              </div>
              <div class="detail-item">
                <span class="label">分类：</span>
                <el-tag size="small">{{ selectedFormula.category?.name }}</el-tag>
              </div>
              <div class="detail-item">
                <span class="label">难度：</span>
                <el-tag :type="difficultyTagType(selectedFormula.difficulty)" size="small">
                  {{ difficultyLabel(selectedFormula.difficulty) }}
                </el-tag>
              </div>
              <div v-if="selectedFormula.description" class="detail-item">
                <span class="label">描述：</span>
                <span>{{ selectedFormula.description }}</span>
              </div>
              <div v-if="selectedFormula.thumbnail" class="detail-thumbnail">
                <img :src="selectedFormula.thumbnail" :alt="selectedFormula.name" />
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="16">
            <div class="detail-demo">
              <h4>3D演示</h4>
              <CubeDemo :formula="selectedFormula" />
            </div>
          </el-col>
        </el-row>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <FormulaEditor 
      :visible="showEditor" 
      :edit-formula="editFormula"
      @close="handleEditorClose"
      @success="handleFormulaSuccess"
    />
  </div>
</template>

<script setup>
/**
 * CollectionView.vue - 我的收藏/公式视图
 *
 * 核心职责：
 * 1. 展示当前用户的收藏公式列表和自创公式列表
 * 2. 支持 Tab 切换：我的收藏 / 我的公式
 * 3. 支持分类、难度、关键词筛选
 * 4. 支持公式详情弹窗（含 3D 演示）
 * 5. 支持自创公式的编辑和添加
 *
 * 功能特性：
 *   - 树形分类筛选（按方法/阶段分组）
 *   - 多选难度筛选（基础/进阶/困难）
 *   - 自创公式支持编辑权限校验（仅作者可编辑）
 *   - 空状态引导用户去公式库收藏或添加公式
 *
 * 设计要点：
 *   - 收藏和自创公式共用筛选逻辑，通过 activeTab 区分数据源
 *   - 分类树由 buildCategoryTree 构建，按 method 分组
 *   - 列表数据兼容分页格式（res.data.results）和数组格式
 */

import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Picture, Star } from '@element-plus/icons-vue';
import { getFormulaCategories, getMyCollections, removeCollection, getMyCustomFormulas } from '../../api/formula';
import CubeDemo from '../../components/formula/CubeDemo.vue';
import FormulaEditor from '../../components/formula/FormulaEditor.vue';

/** 分类列表（原始数据） */
const categoryList = ref([]);
/** 分类树（树形结构，用于 UI 展示） */
const categoryTree = ref([]);
/** 公式列表数据 */
const formulaList = ref([]);
/** 总数 */
const total = ref(0);
/** 当前页码 */
const currentPage = ref(1);
/** 每页数量 */
const pageSize = ref(12);
/** 选中的分类 ID */
const selectedCategory = ref(null);
/** 选中的难度列表 */
const selectedDifficulties = ref([]);
/** 搜索关键词 */
const searchKeyword = ref('');
/** 排序方式 */
const sortBy = ref('default');
/** 详情弹窗显示状态 */
const showDetailDialog = ref(false);
/** 选中的公式对象 */
const selectedFormula = ref(null);
/** 当前激活的 Tab：collections / my_formulas */
const activeTab = ref('collections');
/** 编辑器显示状态 */
const showEditor = ref(false);
/** 正在编辑的公式 */
const editFormula = ref(null);

/**
 * 难度等级标签文本
 *
 * @param {number} level - 难度等级（1-3）
 * @returns {string} 标签文本
 */
const difficultyLabel = (level) => {
  if (level === 1) return '基础';
  if (level === 2) return '进阶';
  return '困难';
};

/**
 * 难度等级标签颜色
 *
 * @param {number} level - 难度等级
 * @returns {string} Element Plus tag 类型
 */
const difficultyTagType = (level) => {
  if (level === 1) return 'success';
  if (level === 2) return 'warning';
  return 'danger';
};

/**
 * 构建分类树形结构
 *
 * 将扁平分类列表转换为按 method 分组的树形结构。
 * 根节点为方法名（如"三阶层先法"），子节点为阶段名（如"F2L"）。
 *
 * @param {Array} categories - 分类列表
 * @returns {Array} 树形结构
 */
const buildCategoryTree = (categories) => {
  const methods = {};
  categories.forEach(cat => {
    if (!methods[cat.method]) {
      methods[cat.method] = {
        id: `method_${cat.method}`,
        name: `${cat.order}阶 - ${cat.method}法`,
        children: []
      };
    }
    methods[cat.method].children.push({
      id: cat.id,
      name: cat.phase,
      raw: cat
    });
  });
  return Object.values(methods);
};

/**
 * 分类点击处理
 *
 * @param {Object} data - 树节点数据（raw 存在表示具体分类，否则为方法分组）
 */
const handleCategoryClick = (data) => {
  if (data.raw) {
    selectedCategory.value = data.raw.id;
  } else {
    selectedCategory.value = null;
  }
  currentPage.value = 1;
  if (activeTab.value === 'collections') {
    loadCollections();
  } else {
    loadMyFormulas();
  }
};

/**
 * 公式点击查看详情
 *
 * @param {Object} formula - 公式对象
 */
const handleFormulaClick = (formula) => {
  selectedFormula.value = formula;
  showDetailDialog.value = true;
};

/**
 * 取消收藏
 *
 * @param {Object} formula - 公式对象
 */
const removeCollectionItem = async (formula) => {
  try {
    await removeCollection(formula.id);
    formulaList.value = formulaList.value.filter(f => f.id !== formula.id);
    total.value--;
    ElMessage.success('取消收藏成功');
  } catch (error) {
    ElMessage.error('取消收藏失败');
  }
};

/**
 * 判断是否为公式作者
 *
 * @param {Object} formula - 公式对象
 * @returns {boolean} 当前用户是否为作者
 */
const isFormulaAuthor = (formula) => {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  return user && formula.author && formula.author.id === user.id;
};

/** 打开编辑器编辑公式 */
const handleEditFormula = (formula) => {
  editFormula.value = formula;
  showEditor.value = true;
};

/** 打开编辑器添加新公式 */
const handleAddFormula = () => {
  editFormula.value = null;
  showEditor.value = true;
};

/** Tab 切换处理 */
const handleTabChange = () => {
  currentPage.value = 1;
  if (activeTab.value === 'collections') {
    loadCollections();
  } else {
    loadMyFormulas();
  }
};

/**
 * 加载分类列表
 */
const loadCategories = async () => {
  try {
    const res = await getFormulaCategories();
    if (res.code === 100) {
      categoryList.value = res.data;
      categoryTree.value = buildCategoryTree(res.data);
    }
  } catch (error) {
    ElMessage.error('加载分类失败');
  }
};

/**
 * 加载收藏公式列表
 *
 * 构建筛选参数，请求后端收藏接口。
 */
const loadCollections = async () => {
  const params = {
    page: currentPage.value,
    page_size: pageSize.value
  };
  if (selectedCategory.value) {
    params.category = selectedCategory.value;
  }
  if (selectedDifficulties.value.length > 0) {
    const difficultyMap = { '基础': [1], '进阶': [2], '困难': [3] };
    const difficultyValues = selectedDifficulties.value.flatMap(d => difficultyMap[d] || []);
    params.difficulty = difficultyValues.join(',');
  }
  if (searchKeyword.value.trim()) {
    params.search = searchKeyword.value.trim();
  }
  if (sortBy.value !== 'default') {
    params.ordering = sortBy.value === 'difficulty_asc' ? 'difficulty' : '-difficulty';
  }

  try {
    const res = await getMyCollections(params);
    if (res.code === 100) {
      if (res.data.results) {
        formulaList.value = res.data.results;
        total.value = res.data.count;
      } else {
        formulaList.value = res.data;
        total.value = res.data.length;
      }
    }
  } catch (error) {
    ElMessage.error('加载收藏列表失败');
  }
};

/**
 * 加载自创公式列表
 *
 * 构建筛选参数，请求后端自创公式接口。
 */
const loadMyFormulas = async () => {
  const params = {
    page: currentPage.value,
    page_size: pageSize.value
  };
  if (selectedCategory.value) {
    params.category = selectedCategory.value;
  }
  if (selectedDifficulties.value.length > 0) {
    const difficultyMap = { '基础': [1], '进阶': [2], '困难': [3] };
    const difficultyValues = selectedDifficulties.value.flatMap(d => difficultyMap[d] || []);
    params.difficulty = difficultyValues.join(',');
  }
  if (searchKeyword.value.trim()) {
    params.search = searchKeyword.value.trim();
  }
  if (sortBy.value !== 'default') {
    params.ordering = sortBy.value === 'difficulty_asc' ? 'difficulty' : '-difficulty';
  }

  try {
    const res = await getMyCustomFormulas(params);
    if (res.code === 100) {
      if (res.data.results) {
        formulaList.value = res.data.results;
        total.value = res.data.count;
      } else {
        formulaList.value = res.data;
        total.value = res.data.length;
      }
    }
  } catch (error) {
    ElMessage.error('加载我的公式失败');
  }
};

/** 筛选变更处理 */
const handleFilterChange = () => {
  currentPage.value = 1;
  if (activeTab.value === 'collections') {
    loadCollections();
  } else {
    loadMyFormulas();
  }
};

/** 搜索处理 */
const handleSearch = () => {
  currentPage.value = 1;
  if (activeTab.value === 'collections') {
    loadCollections();
  } else {
    loadMyFormulas();
  }
};

/** 排序变更处理 */
const handleSortChange = () => {
  currentPage.value = 1;
  if (activeTab.value === 'collections') {
    loadCollections();
  } else {
    loadMyFormulas();
  }
};

/** 分页变更处理 */
const handlePageChange = (page) => {
  currentPage.value = page;
  if (activeTab.value === 'collections') {
    loadCollections();
  } else {
    loadMyFormulas();
  }
};

/**
 * 公式提交成功回调
 *
 * 显示成功提示并刷新当前列表。
 */
const handleFormulaSuccess = () => {
  ElMessage.success('公式提交成功');
  currentPage.value = 1;
  if (activeTab.value === 'my_formulas') {
    loadMyFormulas();
  } else {
    loadCollections();
  }
};

/** 编辑器关闭回调 */
const handleEditorClose = () => {
  showEditor.value = false;
  editFormula.value = null;
};

onMounted(() => {
  loadCategories();
  loadCollections();
});
</script>

<style scoped>
.formula-library {
  padding: 20px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-card,
.filter-card,
.search-card {
  border-radius: 8px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar-left {
  flex: 1;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.result-count {
  font-size: 14px;
  color: #606266;
}

.formula-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.formula-card {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 8px;
}

.formula-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.formula-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.formula-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.formula-notation {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #e6a23c;
  background: #f5f7fa;
  padding: 6px 10px;
  border-radius: 4px;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.formula-thumbnail {
  width: 100%;
  height: 150px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.formula-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #f5f7fa;
}

.formula-thumbnail.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.formula-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-tag {
  font-size: 12px;
  color: #909399;
}

.collected {
  color: #e6a23c;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.empty-state {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.formula-detail {
  padding: 10px;
}

.detail-thumbnail {
  width: 100%;
  height: 200px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
  background: #f5f7fa;
}

.detail-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-info.compact {
  gap: 8px;
}

.detail-info.compact .detail-item {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.detail-info.compact .detail-item .label {
  font-size: 12px;
  min-width: auto;
}

.detail-info.compact .detail-item code.notation {
  font-size: 13px;
  padding: 3px 8px;
}

.detail-info.compact .detail-thumbnail {
  margin-top: 10px;
  width: 100%;
  height: 120px;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f7fa;
}

.detail-info.compact .detail-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.detail-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.detail-item .label {
  font-size: 14px;
  color: #909399;
  min-width: 70px;
}

.detail-item code.notation {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #e6a23c;
  background: #23232e;
  padding: 4px 12px;
  border-radius: 4px;
}

.detail-demo {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-demo h4 {
  margin: 0;
  font-size: 15px;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}
</style>
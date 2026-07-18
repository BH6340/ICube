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
            <span class="result-count">共 {{ total }} 个公式</span>
            <el-select v-model="sortBy" @change="handleSortChange" style="width: 120px">
              <el-option label="默认排序" value="default" />
              <el-option label="难度升序" value="difficulty_asc" />
              <el-option label="难度降序" value="difficulty_desc" />
            </el-select>
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
                <span class="category-tag">{{ formula.category?.name }}</span>
                <el-button
                    type="text"
                    size="small"
                    @click.stop="toggleCollection(formula)"
                    :icon="isCollected(formula.id) ? 'Star' : 'Star'"
                    :class="{ 'collected': isCollected(formula.id) }"
                >
                  {{ isCollected(formula.id) ? '已收藏' : '收藏' }}
                </el-button>
              </div>
            </el-card>
          </div>

          <div v-if="total > pageSize" class="pagination-wrapper">
            <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total"
              layout="total, prev, pager, next" @current-change="handlePageChange" />
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
  </div>
</template>

<script setup>import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Picture, Star } from '@element-plus/icons-vue';
import { getFormulaCategories, getFormulaList, getMyCollections, addCollection, removeCollection } from '../../api/formula';
import CubeDemo from './CubeDemo.vue';
const categoryList = ref([]);
const categoryTree = ref([]);
const formulaList = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(12);
const selectedCategory = ref(null);
const selectedDifficulties = ref([]);
const searchKeyword = ref('');
const sortBy = ref('default');
const showDetailDialog = ref(false);
const selectedFormula = ref(null);
const collectedFormulaIds = ref([]);
const collectionMap = ref({});
const difficultyLabel = (level) => {
  if (level === 1) return '基础';
  if (level === 2) return '进阶';
  return '困难';
};
const difficultyTagType = (level) => {
  if (level === 1) return 'success';
  if (level === 2) return 'warning';
  return 'danger';
};
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
const handleCategoryClick = (data) => {
  if (data.raw) {
    selectedCategory.value = data.raw.id;
  }
  else {
    selectedCategory.value = null;
  }
  currentPage.value = 1;
  loadFormulas();
};
const handleFilterChange = () => {
  currentPage.value = 1;
  loadFormulas();
};
const handleSearch = () => {
  currentPage.value = 1;
  loadFormulas();
};
const handleSortChange = () => {
  currentPage.value = 1;
  loadFormulas();
};
const handlePageChange = (page) => {
  currentPage.value = page;
  loadFormulas();
};
const handleFormulaClick = (formula) => {
  selectedFormula.value = formula;
  showDetailDialog.value = true;
};
const isCollected = (formulaId) => {
  return collectedFormulaIds.value.includes(formulaId);
};
const loadCollections = async () => {
  try {
    const res = await getMyCollections();
    if (res.code === 100) {
      const formulas = res.data.results || res.data;
      collectedFormulaIds.value = formulas.map(f => f.id);
    }
  } catch (error) {
    console.error('加载收藏列表失败', error);
  }
};
const toggleCollection = async (formula) => {
  if (isCollected(formula.id)) {
    try {
      await removeCollection(formula.id);
      collectedFormulaIds.value = collectedFormulaIds.value.filter(id => id !== formula.id);
      ElMessage.success('取消收藏成功');
    } catch (error) {
      ElMessage.error('取消收藏失败');
    }
  } else {
    try {
      await addCollection(formula.id);
      collectedFormulaIds.value.push(formula.id);
      ElMessage.success('收藏成功');
    } catch (error) {
      ElMessage.error('收藏失败');
    }
  }
};
const loadCategories = async () => {
  try {
    const res = await getFormulaCategories();
    if (res.code === 100) {
      categoryList.value = res.data;
      categoryTree.value = buildCategoryTree(res.data);
    }
  }
  catch (error) {
    ElMessage.error('加载分类失败');
  }
};
const loadFormulas = async () => {
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
    const res = await getFormulaList(params);
    if (res.code === 100) {
      formulaList.value = res.data.results;
      total.value = res.data.count;
    }
  }
  catch (error) {
    ElMessage.error('加载公式失败');
  }
};
onMounted(() => {
  loadCategories();
  loadFormulas();
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

.no-thumbnail {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
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
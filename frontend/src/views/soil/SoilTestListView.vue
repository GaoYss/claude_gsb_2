<template>
  <div class="page">
    <PageHeader title="土壤检测档案"
                description="登记采样日期、点位与检测机构，记录酸碱度、有机质与主要养分，结合作物与绿地类型给出施肥配方">
      <template #actions>
        <el-button v-if="activeTab === 'tests'" type="primary" :icon="'Plus'" @click="testDialog.open()">
          登记检测档案
        </el-button>
        <el-button v-else type="primary" :icon="'Plus'" @click="fertDialog.open()">
          登记施肥作业
        </el-button>
      </template>
    </PageHeader>

    <el-tabs v-model="activeTab" class="panel">
      <!-- ===================================================== 检测档案 -->
      <el-tab-pane label="检测档案" name="tests">
        <div class="filter-bar">
          <el-input v-model="testFilters.keyword" placeholder="编号 / 点位 / 机构 / 作物" clearable
                    :prefix-icon="'Search'" @keyup.enter="searchTests" @clear="searchTests" />
          <div style="width: 220px">
            <GreenSpaceSelect v-model="testFilters.green_space_id" placeholder="按绿地筛选"
                              @update:model-value="searchTests" />
          </div>
          <el-input v-model="testFilters.lab" placeholder="检测机构" clearable
                    @keyup.enter="searchTests" @clear="searchTests" />
          <el-date-picker v-model="testDateRange" type="daterange" unlink-panels value-format="YYYY-MM-DD"
                          start-placeholder="采样日期起" end-placeholder="采样日期止" @change="onTestDateChange" />
          <el-button type="primary" :icon="'Search'" @click="searchTests">查询</el-button>
          <el-button :icon="'RefreshLeft'" @click="resetTests">重置</el-button>
        </div>
      </el-tab-pane>

      <!-- ===================================================== 施肥作业 -->
      <el-tab-pane label="施肥作业" name="fertilizations">
        <div class="filter-bar">
          <el-input v-model="fertFilters.keyword" placeholder="作业编号 / 肥料 / 人员" clearable
                    :prefix-icon="'Search'" @keyup.enter="searchFerts" @clear="searchFerts" />
          <div style="width: 220px">
            <GreenSpaceSelect v-model="fertFilters.green_space_id" placeholder="按绿地筛选"
                              @update:model-value="searchFerts" />
          </div>
          <el-select v-model="fertFilters.method" placeholder="施肥方式" clearable @change="searchFerts">
            <el-option v-for="item in methodOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-date-picker v-model="fertDateRange" type="daterange" unlink-panels value-format="YYYY-MM-DD"
                          start-placeholder="施肥日期起" end-placeholder="施肥日期止" @change="onFertDateChange" />
          <el-button type="primary" :icon="'Search'" @click="searchFerts">查询</el-button>
          <el-button :icon="'RefreshLeft'" @click="resetFerts">重置</el-button>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 检测档案统计 -->
    <div v-if="activeTab === 'tests'" class="stat-grid">
      <StatCard label="检测档案" :value="formatNumber(testSummary?.total_count ?? 0)" unit="份"
                hint="当前筛选条件下" icon="Document" />
      <StatCard label="平均酸碱度" :value="formatNumber(testSummary?.avg?.ph)"
                :hint="phHint" tone="info" icon="MagicStick" />
      <StatCard label="平均有机质" :value="formatNumber(testSummary?.avg?.organic_matter)"
                unit="g/kg" hint="土壤肥力基础指标" icon="Coffee" />
      <StatCard label="平均碱解氮 / 有效磷 / 速效钾"
                :value="nutrientText"
                hint="单位 mg/kg" icon="Histogram" />
    </div>

    <!-- 施肥作业统计 -->
    <div v-else class="stat-grid">
      <StatCard label="施肥作业" :value="formatNumber(fertSummary?.total_count ?? 0)" unit="次"
                hint="当前筛选条件下" icon="Sunny" />
      <StatCard label="实际用量合计" :value="formatNumber(fertSummary?.total_actual_dose ?? 0)"
                :hint="`建议用量合计 ${formatNumber(fertSummary?.total_planned_dose ?? 0)}`"
                tone="info" icon="ScaleToOriginal" />
      <StatCard label="引用配方作业" :value="formatNumber(fertSummary?.referenced_count ?? 0)" unit="次"
                :hint="`占比 ${formatNumber(fertSummary?.reference_rate ?? 0)}%`" icon="Connection" />
      <StatCard label="执行偏差" :value="deviationText"
                hint="实际用量相对建议用量" icon="DataAnalysis" />
    </div>

    <!-- 检测档案表格 -->
    <div v-if="activeTab === 'tests'" class="panel">
      <div class="table-toolbar">
        <span class="summary-text">
          共 <strong>{{ testMeta.total }}</strong> 份检测档案，点击编号查看档案详情与历次对比
        </span>
        <el-button :icon="'Refresh'" text @click="loadTests">刷新</el-button>
      </div>
      <el-table :data="testItems" v-loading="testLoading" border stripe>
        <el-table-column prop="test_no" label="档案编号" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="testDetail.open(row.id)">{{ row.test_no }}</el-button>
          </template>
        </el-table-column>
        <el-table-column label="所属绿地" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.green_space?.name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="sample_date" label="采样日期" width="105" />
        <el-table-column prop="sample_point" label="采样点位" min-width="130" show-overflow-tooltip />
        <el-table-column label="pH" width="90" align="center">
          <template #default="{ row }">
            <span :class="indicatorClass(row.grades?.ph)">{{ formatNumber(row.ph) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="有机质" width="100" align="center">
          <template #default="{ row }">
            <span :class="indicatorClass(row.grades?.organic_matter)">{{ formatNumber(row.organic_matter) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="碱解氮" width="90" align="center">
          <template #default="{ row }">
            <span :class="indicatorClass(row.grades?.alkaline_n)">{{ formatNumber(row.alkaline_n) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="有效磷" width="90" align="center">
          <template #default="{ row }">
            <span :class="indicatorClass(row.grades?.available_p)">{{ formatNumber(row.available_p) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="速效钾" width="90" align="center">
          <template #default="{ row }">
            <span :class="indicatorClass(row.grades?.available_k)">{{ formatNumber(row.available_k) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="lab" label="检测机构" min-width="160" show-overflow-tooltip />
        <el-table-column prop="target_crop" label="目标作物" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.target_crop || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="testDialog.open(row)">编辑</el-button>
            <el-button link type="success" @click="registerFertFromTest(row)">施肥</el-button>
            <el-button link type="danger" @click="removeTest(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        class="pager"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="testMeta.total"
        :current-page="testMeta.page"
        :page-size="testMeta.page_size"
        :page-sizes="[10, 20, 50]"
        @current-change="handleTestPage"
        @size-change="handleTestSize"
      />
    </div>

    <!-- 施肥作业表格 -->
    <div v-else class="panel">
      <div class="table-toolbar">
        <span class="summary-text">
          共 <strong>{{ fertMeta.total }}</strong> 次施肥作业，
          实际用量合计 <strong>{{ formatNumber(fertSummary?.total_actual_dose ?? 0) }}</strong>
        </span>
        <el-button :icon="'Refresh'" text @click="loadFerts">刷新</el-button>
      </div>
      <el-table :data="fertItems" v-loading="fertLoading" border stripe>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-detail">
              <span><b>引用检测档案：</b>{{ row.soil_test ? row.soil_test.test_no : '未引用（独立登记）' }}</span>
              <span><b>关联养护记录：</b>{{ row.record ? `${row.record.record_no}（${formatDate(row.record.record_date)}）` : '未关联' }}</span>
              <span><b>建议用量：</b>{{ formatNumber(row.planned_dose) }} {{ row.planned_unit_label || '' }}</span>
              <span><b>施肥方式：</b>{{ row.method_label || '-' }}</span>
              <span><b>施肥人员：</b>{{ row.operator || '-' }}</span>
              <span v-if="row.remark"><b>备注：</b>{{ row.remark }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="fert_no" label="作业编号" width="150" />
        <el-table-column label="所属绿地" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.green_space?.name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="fert_date" label="施肥日期" width="105" />
        <el-table-column prop="product_name" label="肥料名称" min-width="140" show-overflow-tooltip />
        <el-table-column label="建议用量" width="130" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.planned_dose) }} {{ row.planned_unit_label || '' }}
          </template>
        </el-table-column>
        <el-table-column label="实际用量" width="140" align="right">
          <template #default="{ row }">
            <strong>{{ formatNumber(row.actual_dose) }}</strong> {{ row.actual_unit_label }}
          </template>
        </el-table-column>
        <el-table-column label="执行情况" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.planned_dose === null || row.planned_dose === undefined"
                    type="info" size="small" effect="plain">无配方</el-tag>
            <el-tag v-else :type="executionTag(row).type" size="small">
              {{ executionTag(row).text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="fertDialog.open(row)">编辑</el-button>
            <el-button link type="danger" @click="removeFert(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        class="pager"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="fertMeta.total"
        :current-page="fertMeta.page"
        :page-size="fertMeta.page_size"
        :page-sizes="[10, 20, 50]"
        @current-change="handleFertPage"
        @size-change="handleFertSize"
      />
    </div>

    <SoilTestFormDialog ref="testDialog" @saved="loadTests" />
    <SoilTestDetailDialog ref="testDetail" @register-fert="onRegisterFert" />
    <FertilizationFormDialog ref="fertDialog" @saved="loadFerts" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { fertilizationApi, soilTestApi } from '@/api'
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { useMetaStore } from '@/stores/meta'
import { formatDate, formatNumber } from '@/utils/format'

import FertilizationFormDialog from './FertilizationFormDialog.vue'
import SoilTestDetailDialog from './SoilTestDetailDialog.vue'
import SoilTestFormDialog from './SoilTestFormDialog.vue'

const route = useRoute()
const metaStore = useMetaStore()
const { options: methodOptions } = useEnumOptions('fert_method')

const activeTab = ref(route.query.tab === 'fertilizations' ? 'fertilizations' : 'tests')

const testDialog = ref(null)
const testDetail = ref(null)
const fertDialog = ref(null)

// ----------------------------------------------------------- 检测档案数据
const testItems = ref([])
const testMeta = reactive({ page: 1, page_size: 10, total: 0, pages: 0 })
const testSummary = ref(null)
const testLoading = ref(false)
const testFilters = reactive({
  keyword: '',
  green_space_id: route.query.green_space_id ? Number(route.query.green_space_id) : null,
  lab: '',
  date_from: '',
  date_to: '',
})
const testDateRange = ref([])

// ----------------------------------------------------------- 施肥作业数据
const fertItems = ref([])
const fertMeta = reactive({ page: 1, page_size: 10, total: 0, pages: 0 })
const fertSummary = ref(null)
const fertLoading = ref(false)
const fertFilters = reactive({
  keyword: '',
  green_space_id: route.query.green_space_id ? Number(route.query.green_space_id) : null,
  method: '',
  date_from: '',
  date_to: '',
})
const fertDateRange = ref([])

function buildParams(filters, meta) {
  const params = { page: meta.page, page_size: meta.page_size }
  Object.entries(filters).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') return
    params[key] = value
  })
  return params
}

async function loadTests() {
  testLoading.value = true
  try {
    const data = await soilTestApi.list(buildParams(testFilters, testMeta))
    testItems.value = data?.items || []
    testSummary.value = data?.summary || null
    Object.assign(testMeta, data.meta)
  } finally {
    testLoading.value = false
  }
}

async function loadFerts() {
  fertLoading.value = true
  try {
    const data = await fertilizationApi.list(buildParams(fertFilters, fertMeta))
    fertItems.value = data?.items || []
    fertSummary.value = data?.summary || null
    Object.assign(fertMeta, data.meta)
  } finally {
    fertLoading.value = false
  }
}

function searchTests() { testMeta.page = 1; return loadTests() }
function searchFerts() { fertMeta.page = 1; return loadFerts() }
function handleTestPage(page) { testMeta.page = page; loadTests() }
function handleTestSize(size) { testMeta.page_size = size; testMeta.page = 1; loadTests() }
function handleFertPage(page) { fertMeta.page = page; loadFerts() }
function handleFertSize(size) { fertMeta.page_size = size; fertMeta.page = 1; loadFerts() }

function onTestDateChange(value) {
  testFilters.date_from = value?.[0] || ''
  testFilters.date_to = value?.[1] || ''
  searchTests()
}

function onFertDateChange(value) {
  fertFilters.date_from = value?.[0] || ''
  fertFilters.date_to = value?.[1] || ''
  searchFerts()
}

function resetTests() {
  testDateRange.value = []
  Object.assign(testFilters, { keyword: '', green_space_id: null, lab: '', date_from: '', date_to: '' })
  searchTests()
}

function resetFerts() {
  fertDateRange.value = []
  Object.assign(fertFilters, { keyword: '', green_space_id: null, method: '', date_from: '', date_to: '' })
  searchFerts()
}

// ----------------------------------------------------------- 展示派生
const phHint = computed(() => {
  const ph = testSummary.value?.avg?.ph
  if (ph === null || ph === undefined) return '暂无数据'
  if (ph < 5.5) return '整体偏酸，需调酸改土'
  if (ph > 8.5) return '整体偏碱，需调碱改良'
  return '酸碱度总体适宜'
})

const nutrientText = computed(() => {
  const avg = testSummary.value?.avg
  if (!avg || avg.alkaline_n === null) return '-'
  return `${formatNumber(avg.alkaline_n)} / ${formatNumber(avg.available_p)} / ${formatNumber(avg.available_k)}`
})

const deviationText = computed(() => {
  const planned = fertSummary.value?.total_planned_dose
  const actual = fertSummary.value?.total_actual_dose
  if (!planned) return '-'
  const percent = ((actual - planned) / planned) * 100
  return `${percent > 0 ? '+' : ''}${percent.toFixed(1)}%`
})

function indicatorClass(grade) {
  if (!grade) return ''
  if (grade === 'medium') return 'grade-good'
  if (grade === 'low' || grade === 'high') return 'grade-warn'
  return 'grade-bad'
}

function executionTag(row) {
  if (row.planned_dose === null || row.planned_dose === undefined) {
    return { type: 'info', text: '无配方' }
  }
  const ratio = row.actual_dose / row.planned_dose
  if (Math.abs(ratio - 1) <= 0.1) return { type: 'success', text: '按方执行' }
  return ratio > 1 ? { type: 'warning', text: '超量' } : { type: 'warning', text: '减量' }
}

function registerFertFromTest(row) {
  activeTab.value = 'fertilizations'
  fertDialog.value?.open(null, { green_space: row.green_space })
}

function onRegisterFert(detail) {
  testDetail.value?.close()
  activeTab.value = 'fertilizations'
  fertDialog.value?.open(null, { green_space: detail.green_space })
}

async function removeTest(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除检测档案「${row.test_no}」吗？其配方明细将一并删除，已登记的施肥作业会保留但解除引用。`,
      '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
    await soilTestApi.remove(row.id)
    ElMessage.success('土壤检测档案已删除')
    await loadTests()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}

async function removeFert(row) {
  try {
    await ElMessageBox.confirm(`确认删除施肥作业「${row.fert_no}」吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await fertilizationApi.remove(row.id)
    ElMessage.success('施肥作业已删除')
    await loadFerts()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}

watch(activeTab, (tab) => {
  if (tab === 'fertilizations' && !fertItems.value.length) loadFerts()
})

onMounted(async () => {
  await metaStore.ensureIndicators()
  await loadTests()
})
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.expand-detail {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 6px 16px;
  padding: 4px 12px;
  color: #606266;
  font-size: 13px;
}

.grade-good {
  color: #2f855a;
  font-weight: 600;
}

.grade-warn {
  color: #e6a23c;
  font-weight: 600;
}

.grade-bad {
  color: #f56c6c;
  font-weight: 600;
}
</style>

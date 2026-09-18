<template>
  <div class="page" v-loading="loading">
    <PageHeader :title="space.name || '绿地档案'" :description="`绿地编号 ${space.code || '-'}`">
      <template #tag>
        <EnumTag v-if="space.status" group="green_space_status" :value="space.status" :label="space.status_label" />
      </template>
      <template #actions>
        <el-button :icon="'Back'" @click="router.push('/green-spaces')">返回台账</el-button>
        <el-button type="primary" :icon="'Edit'" @click="formDialog.open(space)">编辑台账</el-button>
      </template>
    </PageHeader>

    <div class="panel">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="所属行政区">{{ space.district || '-' }}</el-descriptions-item>
        <el-descriptions-item label="绿地类型">
          <EnumTag group="green_space_type" :value="space.green_type" :label="space.green_type_label" />
        </el-descriptions-item>
        <el-descriptions-item label="养护等级">
          <EnumTag group="maintenance_grade" :value="space.maintenance_grade" :label="space.maintenance_grade_label" />
        </el-descriptions-item>
        <el-descriptions-item label="绿地面积">{{ formatArea(space.area_sqm) }}</el-descriptions-item>
        <el-descriptions-item label="养护负责人">{{ space.manager || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ space.contact_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="建成日期">{{ formatDate(space.established_date) }}</el-descriptions-item>
        <el-descriptions-item label="详细地址" :span="2">{{ space.address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="主要植物" :span="3">{{ space.plant_summary || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ space.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="stat-grid">
      <StatCard label="养护记录" :value="formatNumber(statistics.record_count)" unit="条"
                :hint="`累计工时 ${formatHours(statistics.total_work_hours)}`" icon="Notebook" />
      <StatCard label="最近养护日期" :value="formatDate(statistics.last_maintenance_date)"
                :hint="statistics.is_maintenance_overdue ? '已超过 30 天未养护' : '养护节奏正常'"
                :tone="statistics.is_maintenance_overdue ? 'warning' : 'default'" icon="Calendar" />
      <StatCard label="绿植更换" :value="formatNumber(statistics.replacement_quantity)"
                :hint="`共 ${formatNumber(statistics.replacement_count)} 次，金额 ${formatCurrency(statistics.replacement_amount)}`"
                icon="Cherry" />
      <StatCard label="土壤检测" :value="formatNumber(soilTestCount)" unit="份"
                :hint="latestSoil ? `最近 ${formatDate(latestSoil.sample_date)} · pH ${formatNumber(latestSoil.ph_value)}` : '暂无检测档案'"
                :tone="latestSoil && latestSoil.ph_level !== 'neutral' ? 'warning' : 'default'"
                icon="Histogram" />
      <StatCard label="养护任务" :value="formatNumber(taskTotal)" unit="项"
                :hint="`已完成 ${statistics.task_status.completed || 0} 项，进行中 ${(statistics.task_status.in_progress || 0) + (statistics.task_status.pending || 0)} 项`"
                tone="info" icon="Tickets" />
    </div>

    <div class="panel">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="近期养护任务" name="tasks">
          <div class="tab-actions">
            <el-button link type="primary" @click="goList('tasks')">查看全部养护任务</el-button>
          </div>
          <el-table :data="recentTasks" size="small" empty-text="暂无养护任务">
            <el-table-column prop="task_no" label="任务编号" width="160" />
            <el-table-column prop="title" label="任务名称" min-width="160" show-overflow-tooltip />
            <el-table-column label="养护类型" width="120">
              <template #default="{ row }">
                <EnumTag group="task_type" :value="row.task_type" :label="row.task_type_label" />
              </template>
            </el-table-column>
            <el-table-column prop="plan_date" label="计划日期" width="110" />
            <el-table-column label="优先级" width="90">
              <template #default="{ row }">
                <EnumTag group="task_priority" :value="row.priority" :label="row.priority_label" />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <EnumTag group="task_status" :value="row.status" :label="row.status_label" />
              </template>
            </el-table-column>
            <el-table-column prop="executor" label="执行班组" width="120">
              <template #default="{ row }">{{ row.executor || '-' }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="近期养护记录" name="records">
          <div class="tab-actions">
            <el-button link type="primary" @click="goList('records')">查看全部养护记录</el-button>
          </div>
          <el-table :data="recentRecords" size="small" empty-text="暂无养护记录">
            <el-table-column prop="record_no" label="记录编号" width="160" />
            <el-table-column prop="record_date" label="养护日期" width="110" />
            <el-table-column prop="work_content" label="作业内容" min-width="220" show-overflow-tooltip />
            <el-table-column prop="worker" label="作业人员" width="110">
              <template #default="{ row }">{{ row.worker || '-' }}</template>
            </el-table-column>
            <el-table-column label="工时" width="90">
              <template #default="{ row }">{{ formatHours(row.work_hours) }}</template>
            </el-table-column>
            <el-table-column label="质量评定" width="100">
              <template #default="{ row }">
                <EnumTag group="quality_result" :value="row.quality_result" :label="row.quality_result_label" />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="近期绿植更换" name="replacements">
          <div class="tab-actions">
            <el-button link type="primary" @click="goList('replacements')">查看全部更换记录</el-button>
          </div>
          <el-table :data="recentReplacements" size="small" empty-text="暂无更换记录">
            <el-table-column prop="replacement_no" label="编号" width="160" />
            <el-table-column prop="replace_date" label="更换日期" width="110" />
            <el-table-column prop="plant_name" label="植株名称" width="130" />
            <el-table-column prop="spec" label="规格" width="130">
              <template #default="{ row }">{{ row.spec || '-' }}</template>
            </el-table-column>
            <el-table-column label="数量" width="110">
              <template #default="{ row }">{{ formatNumber(row.quantity) }} {{ row.unit_label }}</template>
            </el-table-column>
            <el-table-column label="更换原因" width="120">
              <template #default="{ row }">
                <EnumTag group="replacement_reason" :value="row.reason" :label="row.reason_label" />
              </template>
            </el-table-column>
            <el-table-column label="金额" width="120" align="right">
              <template #default="{ row }">{{ formatCurrency(row.amount) }}</template>
            </el-table-column>
          </el-table>

          <div v-if="replacementSummary.length" class="replacement-summary">
            <span class="summary-text">更换原因汇总：</span>
            <el-tag v-for="item in replacementSummary" :key="item.reason" class="summary-tag" type="info" effect="plain">
              {{ item.reason_label }} {{ formatNumber(item.quantity) }} 单位 / {{ formatCurrency(item.amount) }}
            </el-tag>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="`土壤检测${soilTestCount ? `（${soilTestCount}）` : ''}`" name="soil">
          <div class="tab-actions">
            <el-button type="primary" size="small" :icon="'Plus'" @click="openSoilForm">登记土壤检测</el-button>
            <el-button link type="primary" @click="goList('soil')">查看全部检测档案</el-button>
          </div>

          <div v-if="latestSoil" class="latest-soil">
            <div class="latest-soil__head">
              <span class="panel-title">最近一次检测 · {{ latestSoil.test_no }}</span>
              <span class="summary-text">{{ formatDate(latestSoil.sample_date) }} · {{ latestSoil.lab_org }}</span>
            </div>
            <div class="latest-soil__indicators">
              <div class="soil-indicator">
                <span class="soil-indicator__label">pH</span>
                <span class="soil-indicator__value">{{ formatNumber(latestSoil.ph_value) }}</span>
                <EnumTag group="ph_level" :value="latestSoil.ph_level" :label="latestSoil.ph_level_label" />
              </div>
              <div class="soil-indicator">
                <span class="soil-indicator__label">有机质 g/kg</span>
                <span class="soil-indicator__value">{{ formatNumber(latestSoil.organic_matter) }}</span>
                <EnumTag group="organic_level" :value="latestSoil.organic_level" :label="latestSoil.organic_level_label" />
              </div>
              <div class="soil-indicator">
                <span class="soil-indicator__label">碱解氮</span>
                <span class="soil-indicator__value">{{ formatNumber(latestSoil.alkali_nitrogen) }}</span>
                <EnumTag group="nutrient_level" :value="latestSoil.nitrogen_level" :label="latestSoil.nitrogen_level_label" />
              </div>
              <div class="soil-indicator">
                <span class="soil-indicator__label">有效磷</span>
                <span class="soil-indicator__value">{{ formatNumber(latestSoil.available_phosphorus) }}</span>
                <EnumTag group="nutrient_level" :value="latestSoil.phosphorus_level" :label="latestSoil.phosphorus_level_label" />
              </div>
              <div class="soil-indicator">
                <span class="soil-indicator__label">速效钾</span>
                <span class="soil-indicator__value">{{ formatNumber(latestSoil.available_potassium) }}</span>
                <EnumTag group="nutrient_level" :value="latestSoil.potassium_level" :label="latestSoil.potassium_level_label" />
              </div>
            </div>
            <div class="latest-soil__formula">
              <span class="summary-text">
                <b>推荐配方：</b>{{ latestSoil.fertilizer_name || '-' }}
                （{{ latestSoil.nutrient_ratio || '-' }}），
                {{ formatNumber(latestSoil.dosage_per_sqm) }} kg/㎡，
                {{ latestSoil.application_method_label || '-' }}，
                已引用 {{ latestSoil.application_count || 0 }} 次
              </span>
            </div>
          </div>
          <el-empty v-else description="该绿地暂无土壤检测档案" :image-size="60" />

          <el-table :data="recentSoilTests" size="small" empty-text="暂无检测档案" class="soil-table">
            <el-table-column prop="test_no" label="档案编号" width="160" />
            <el-table-column prop="sample_date" label="采样日期" width="105" />
            <el-table-column prop="sample_point" label="采样点位" min-width="150" show-overflow-tooltip />
            <el-table-column label="pH" width="90">
              <template #default="{ row }">
                {{ formatNumber(row.ph_value) }}
                <EnumTag group="ph_level" :value="row.ph_level" :label="row.ph_level_label" />
              </template>
            </el-table-column>
            <el-table-column label="有机质" width="100">
              <template #default="{ row }">{{ formatNumber(row.organic_matter) }}</template>
            </el-table-column>
            <el-table-column label="氮/磷/钾" min-width="160">
              <template #default="{ row }">
                {{ formatNumber(row.alkali_nitrogen) }} /
                {{ formatNumber(row.available_phosphorus) }} /
                {{ formatNumber(row.available_potassium) }}
              </template>
            </el-table-column>
            <el-table-column label="推荐肥料" min-width="130" show-overflow-tooltip>
              <template #default="{ row }">{{ row.fertilizer_name || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button link type="primary" @click="openSoilDetail(row)">档案/对比</el-button>
                <el-button link type="primary" @click="openSoilForm(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <GreenSpaceFormDialog ref="formDialog" @saved="load" />
    <SoilTestFormDialog ref="soilFormDialog" @saved="load" />
    <SoilTestDetailDrawer ref="soilDetailDrawer" @changed="load" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { greenSpaceApi } from '@/api'
import EnumTag from '@/components/common/EnumTag.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import { formatArea, formatCurrency, formatDate, formatHours, formatNumber } from '@/utils/format'

import GreenSpaceFormDialog from './GreenSpaceFormDialog.vue'
import SoilTestDetailDrawer from '@/views/soil/SoilTestDetailDrawer.vue'
import SoilTestFormDialog from '@/views/soil/SoilTestFormDialog.vue'

const route = useRoute()
const router = useRouter()
const formDialog = ref(null)
const soilFormDialog = ref(null)
const soilDetailDrawer = ref(null)
const loading = ref(false)
const activeTab = ref(route.query.tab === 'soil' ? 'soil' : 'tasks')

const space = ref({})
const statistics = ref({ task_status: {}, record_count: 0, total_work_hours: 0, replacement_count: 0, replacement_quantity: 0, replacement_amount: 0 })
const recentTasks = ref([])
const recentRecords = ref([])
const recentReplacements = ref([])
const recentSoilTests = ref([])
const latestSoil = ref(null)
const soilTestTotal = ref(0)
const replacementSummary = ref([])

const taskTotal = computed(() =>
  Object.values(statistics.value.task_status || {}).reduce((sum, value) => sum + value, 0),
)
const soilTestCount = computed(() => soilTestTotal.value)

async function load() {
  loading.value = true
  try {
    const data = await greenSpaceApi.profile(route.params.id)
    space.value = data.green_space || {}
    statistics.value = data.statistics || {}
    recentTasks.value = data.recent_tasks || []
    recentRecords.value = data.recent_records || []
    recentReplacements.value = data.recent_replacements || []
    recentSoilTests.value = data.recent_soil_tests || []
    latestSoil.value = data.latest_soil_test || null
    soilTestTotal.value = data.soil_test_count || 0
    replacementSummary.value = data.replacement_summary || []
  } finally {
    loading.value = false
  }
}

const LIST_ROUTES = {
  tasks: 'task-list',
  records: 'record-list',
  replacements: 'replacement-list',
  soil: 'soil-test-list',
}

function goList(name) {
  router.push({ name: LIST_ROUTES[name], query: { green_space_id: route.params.id } })
}

function openSoilForm(row = null) {
  const preset = space.value?.code
    ? { id: space.value.id, code: space.value.code, name: space.value.name }
    : null
  soilFormDialog.value.open(row, { greenSpaceId: Number(route.params.id), preset })
}

function openSoilDetail(row) {
  soilDetailDrawer.value.open(row.id)
}

onMounted(load)
</script>

<style scoped>
.tab-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.replacement-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.summary-tag {
  margin-right: 4px;
}

.latest-soil {
  border: 1px solid var(--gs-border);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.latest-soil__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.latest-soil__indicators {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 10px;
}

.soil-indicator {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.soil-indicator__label {
  color: #909399;
  font-size: 12px;
}

.soil-indicator__value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.soil-table {
  margin-top: 8px;
}
</style>

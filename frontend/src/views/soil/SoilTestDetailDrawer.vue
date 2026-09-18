<template>
  <el-drawer :model-value="visible" size="780px"
             :title="detail.test_no ? `土壤检测档案 · ${detail.test_no}` : '土壤检测档案'"
             @update:model-value="close">
    <div v-loading="loading" class="drawer-body">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="所属绿地" :span="2">
          {{ detail.green_space ? `${detail.green_space.code} ${detail.green_space.name}` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="采样日期">{{ formatDate(detail.sample_date) }}</el-descriptions-item>
        <el-descriptions-item label="采样点位">{{ detail.sample_point }}</el-descriptions-item>
        <el-descriptions-item label="采样深度">
          {{ detail.sample_depth != null ? `${detail.sample_depth} cm` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="土壤质地">
          {{ detail.soil_texture_label || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="检测机构" :span="2">{{ detail.lab_org }}</el-descriptions-item>
        <el-descriptions-item label="报告编号">{{ detail.report_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="登记人">{{ detail.operator || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="section-title">理化检测指标</div>
      <div class="indicator-grid">
        <div class="indicator">
          <div class="indicator__label">酸碱度 pH</div>
          <div class="indicator__value">{{ formatNumber(detail.ph_value) }}</div>
          <EnumTag group="ph_level" :value="detail.ph_level" :label="detail.ph_level_label" />
        </div>
        <div class="indicator">
          <div class="indicator__label">有机质 (g/kg)</div>
          <div class="indicator__value">{{ formatNumber(detail.organic_matter) }}</div>
          <EnumTag group="organic_level" :value="detail.organic_level" :label="detail.organic_level_label" />
        </div>
        <div class="indicator">
          <div class="indicator__label">碱解氮 (mg/kg)</div>
          <div class="indicator__value">{{ formatNumber(detail.alkali_nitrogen) }}</div>
          <EnumTag group="nutrient_level" :value="detail.nitrogen_level"
                   :label="detail.nitrogen_level_label" />
        </div>
        <div class="indicator">
          <div class="indicator__label">有效磷 (mg/kg)</div>
          <div class="indicator__value">{{ formatNumber(detail.available_phosphorus) }}</div>
          <EnumTag group="nutrient_level" :value="detail.phosphorus_level"
                   :label="detail.phosphorus_level_label" />
        </div>
        <div class="indicator">
          <div class="indicator__label">速效钾 (mg/kg)</div>
          <div class="indicator__value">{{ formatNumber(detail.available_potassium) }}</div>
          <EnumTag group="nutrient_level" :value="detail.potassium_level"
                   :label="detail.potassium_level_label" />
        </div>
        <div class="indicator indicator--muted">
          <div class="indicator__label">容重 / 全盐 / 含水率</div>
          <div class="indicator__sub">
            {{ detail.bulk_density != null ? `${detail.bulk_density} g/cm³` : '-' }} ·
            {{ detail.salinity != null ? `${detail.salinity} g/kg` : '-' }} ·
            {{ detail.moisture != null ? `${detail.moisture}%` : '-' }}
          </div>
        </div>
      </div>

      <div class="table-toolbar">
        <span class="section-title">推荐施肥配方</span>
        <el-button link type="primary" :icon="'Refresh'" @click="regenerate">按检测结果重新生成</el-button>
      </div>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="目标作物/植物" :span="2">{{ detail.target_plants || '-' }}</el-descriptions-item>
        <el-descriptions-item label="肥料">
          {{ detail.fertilizer_name || '-' }}
          <EnumTag v-if="detail.fertilizer_type" group="fertilizer_type"
                   :value="detail.fertilizer_type" :label="detail.fertilizer_type_label" />
        </el-descriptions-item>
        <el-descriptions-item label="养分配比">{{ detail.nutrient_ratio || '-' }}</el-descriptions-item>
        <el-descriptions-item label="建议用量">
          {{ formatNumber(detail.dosage_per_sqm) }} kg/㎡
        </el-descriptions-item>
        <el-descriptions-item label="施肥方式">{{ detail.application_method_label || '-' }}</el-descriptions-item>
        <el-descriptions-item label="施肥频次">{{ detail.application_frequency || '-' }}</el-descriptions-item>
        <el-descriptions-item label="施肥时期">{{ detail.application_period || '-' }}</el-descriptions-item>
        <el-descriptions-item label="配方说明" :span="2">{{ detail.formula_advice || '-' }}</el-descriptions-item>
        <el-descriptions-item label="检测结论" :span="2">{{ detail.conclusion || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="table-toolbar">
        <span class="section-title">施肥作业（引用本配方）</span>
        <el-button type="primary" size="small" :icon="'Plus'" @click="applyDialog.open(null, detail)">
          登记施肥作业
        </el-button>
      </div>
      <el-table :data="detail.applications || []" size="small" border empty-text="该配方尚未被施肥作业引用">
        <el-table-column prop="application_no" label="作业编号" width="150" />
        <el-table-column prop="plan_date" label="计划日期" width="100" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <EnumTag group="application_status" :value="row.status" :label="row.status_label" />
          </template>
        </el-table-column>
        <el-table-column label="计划用量(kg)" width="115" align="right">
          <template #default="{ row }">{{ formatNumber(row.planned_amount) }}</template>
        </el-table-column>
        <el-table-column prop="applied_date" label="施肥日期" width="100" />
        <el-table-column label="实际用量(kg)" width="115" align="right">
          <template #default="{ row }">{{ formatNumber(row.actual_amount) }}</template>
        </el-table-column>
        <el-table-column label="偏差(kg)" width="100" align="right">
          <template #default="{ row }">
            <span :class="deviationClass(row.deviation)">{{ formatSigned(row.deviation) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="applyDialog.open(row, detail)">
              {{ row.status === 'applied' ? '查看/编辑' : '回填' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="comparison && comparison.items.length" class="comparison">
        <div class="table-toolbar">
          <span class="section-title">同绿地多次检测对比</span>
          <span class="comparison__hint">
            共 {{ comparison.items.length }} 次检测，最早 {{ comparison.items[0].sample_date }}
          </span>
        </div>
        <ChartPanel title="酸碱度与有机质变化" hint="pH（左轴） / 有机质 g/kg（右轴）"
                    :option="phOrganicOption" height="240px" />
        <ChartPanel title="主要养分（氮磷钾）变化" hint="单位 mg/kg"
                    :option="nutrientOption" height="240px" />
        <el-table :data="comparison.items" size="small" border class="comparison-table">
          <el-table-column prop="sample_date" label="采样日期" width="105" />
          <el-table-column prop="test_no" label="档案编号" width="150" />
          <el-table-column label="pH" width="80">
            <template #default="{ row }">{{ formatNumber(row.ph_value) }}</template>
          </el-table-column>
          <el-table-column label="有机质" width="90">
            <template #default="{ row }">{{ formatNumber(row.organic_matter) }}</template>
          </el-table-column>
          <el-table-column label="碱解氮" width="90">
            <template #default="{ row }">{{ formatNumber(row.alkali_nitrogen) }}</template>
          </el-table-column>
          <el-table-column label="有效磷" width="90">
            <template #default="{ row }">{{ formatNumber(row.available_phosphorus) }}</template>
          </el-table-column>
          <el-table-column label="速效钾" width="90">
            <template #default="{ row }">{{ formatNumber(row.available_potassium) }}</template>
          </el-table-column>
          <el-table-column label="施肥" width="70" align="center">
            <template #default="{ row }">{{ row.application_count }} 次</template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else-if="!loading" description="该绿地暂无多次检测，无法形成对比" :image-size="60" />
    </div>

    <template #footer>
      <el-button @click="close">关闭</el-button>
    </template>

    <FertilizationApplyDialog ref="applyDialog" @saved="onApplicationSaved" />
  </el-drawer>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { soilTestApi } from '@/api'
import ChartPanel from '@/components/common/ChartPanel.vue'
import EnumTag from '@/components/common/EnumTag.vue'
import { formatDate, formatNumber } from '@/utils/format'

import FertilizationApplyDialog from './FertilizationApplyDialog.vue'

const emit = defineEmits(['changed'])

const visible = ref(false)
const loading = ref(false)
const detail = ref({})
const comparison = ref(null)
const applyDialog = ref(null)
const currentId = ref(null)
const dirty = ref(false)

async function open(id) {
  currentId.value = id
  dirty.value = false
  visible.value = true
  await reload()
}

async function reload() {
  if (!currentId.value) return
  loading.value = true
  try {
    detail.value = await soilTestApi.detail(currentId.value)
    if (detail.value.green_space_id) {
      comparison.value = await soilTestApi.comparison(detail.value.green_space_id)
    }
  } finally {
    loading.value = false
  }
}

function onApplicationSaved() {
  dirty.value = true
  return reload()
}

async function regenerate() {
  try {
    detail.value = await soilTestApi.regeneratePlan(currentId.value)
    dirty.value = true
    ElMessage.success('施肥配方已重新生成')
  } catch {
    // 错误提示由请求层处理
  }
}

function close() {
  visible.value = false
  if (dirty.value) emit('changed')
}

function formatSigned(value) {
  if (value === null || value === undefined) return '-'
  const number = Number(value)
  if (!Number.isFinite(number)) return '-'
  return `${number > 0 ? '+' : ''}${formatNumber(number)}`
}

function deviationClass(value) {
  if (value === null || value === undefined) return ''
  const number = Number(value)
  if (Math.abs(number) < 0.01) return 'deviation--ok'
  return number > 0 ? 'deviation--up' : 'deviation--down'
}

const palette = ['#2f855a', '#dd6b66', '#759aa0', '#e69d2d']

const phOrganicOption = computed(() => {
  const items = comparison.value?.items || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['pH', '有机质'], top: 0 },
    grid: { left: 48, right: 56, top: 36, bottom: 32 },
    xAxis: { type: 'category', data: items.map((item) => item.sample_date) },
    yAxis: [
      { type: 'value', name: 'pH', min: 3, max: 10 },
      { type: 'value', name: 'g/kg', min: 0 },
    ],
    series: [
      {
        name: 'pH', type: 'line', smooth: true, symbolSize: 7,
        data: items.map((item) => item.ph_value),
        itemStyle: { color: palette[1] }, lineStyle: { width: 3 },
      },
      {
        name: '有机质', type: 'line', smooth: true, symbolSize: 7, yAxisIndex: 1,
        data: items.map((item) => item.organic_matter),
        itemStyle: { color: palette[0] }, lineStyle: { width: 3 },
      },
    ],
  }
})

const nutrientOption = computed(() => {
  const items = comparison.value?.items || []
  const seriesDefs = [
    ['碱解氮', 'alkali_nitrogen', palette[0]],
    ['有效磷', 'available_phosphorus', palette[2]],
    ['速效钾', 'available_potassium', palette[3]],
  ]
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: seriesDefs.map(([name]) => name), top: 0 },
    grid: { left: 56, right: 24, top: 36, bottom: 32 },
    xAxis: { type: 'category', data: items.map((item) => item.sample_date) },
    yAxis: { type: 'value', name: 'mg/kg' },
    series: seriesDefs.map(([name, field, color]) => ({
      name, type: 'line', smooth: true, symbolSize: 7,
      data: items.map((item) => item[field]),
      itemStyle: { color }, lineStyle: { width: 2.5 },
    })),
  }
})

defineExpose({ open })
</script>

<style scoped>
.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-title {
  font-weight: 600;
  font-size: 14px;
}

.indicator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.indicator {
  border: 1px solid var(--gs-border);
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.indicator--muted {
  justify-content: center;
}

.indicator__label {
  color: #909399;
  font-size: 12px;
}

.indicator__value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.indicator__sub {
  color: #606266;
  font-size: 13px;
}

.comparison {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comparison__hint {
  color: #909399;
  font-size: 12px;
}

.comparison-table {
  margin-top: -4px;
}

.deviation--up {
  color: #e6a23c;
}

.deviation--down {
  color: #409eff;
}

.deviation--ok {
  color: #67c23a;
}
</style>

<template>
  <el-dialog :model-value="visible"
             :title="detail.test_no ? `土壤检测档案 · ${detail.test_no}` : '土壤检测档案详情'"
             width="900px" top="4vh" @update:model-value="close">
    <div v-loading="loading">
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="所属绿地" :span="2">
          {{ detail.green_space ? `${detail.green_space.code} ${detail.green_space.name}` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="采样日期">{{ formatDate(detail.sample_date) }}</el-descriptions-item>
        <el-descriptions-item label="采样点位">{{ detail.sample_point }}</el-descriptions-item>
        <el-descriptions-item label="采样深度">
          {{ detail.sample_depth !== null ? `${formatNumber(detail.sample_depth)} cm` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="土壤质地">{{ detail.texture_label || '-' }}</el-descriptions-item>
        <el-descriptions-item label="检测机构">{{ detail.lab }}</el-descriptions-item>
        <el-descriptions-item label="报告编号">{{ detail.lab_report_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="目标作物" :span="1">{{ detail.target_crop || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="section-title">检测结果与丰缺评级</div>
      <el-table :data="indicatorRows" size="small" border>
        <el-table-column prop="label" label="检测指标" width="150" />
        <el-table-column label="检测值" width="140">
          <template #default="{ row }">
            {{ formatNumber(row.value) }} <span class="unit">{{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="丰缺等级" width="120">
          <template #default="{ row }">
            <EnumTag v-if="row.grade" group="soil_grade" :value="row.grade" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="与上一次差值" min-width="140">
          <template #default="{ row }">
            <span v-if="row.delta === null || row.delta === undefined">-</span>
            <span v-else :class="deltaClass(row.delta, row.key)">
              {{ row.delta > 0 ? '+' : '' }}{{ formatNumber(row.delta) }} {{ row.unit }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="detail.fert_advice" class="advice-box">
        <b>施肥建议：</b>{{ detail.fert_advice }}
      </div>
      <div v-if="detail.remark" class="advice-box">
        <b>备注：</b>{{ detail.remark }}
      </div>

      <div class="section-title">
        施肥配方
        <el-button v-if="detail.green_space_id" link type="primary" class="add-fert"
                   @click="emit('registerFert', detail)">登记施肥作业</el-button>
      </div>
      <el-table :data="detail.formula_items || []" size="small" border empty-text="暂无配方明细">
        <el-table-column prop="product_name" label="肥料名称" min-width="150" />
        <el-table-column prop="nutrient_ratio" label="养分配比" width="120">
          <template #default="{ row }">{{ row.nutrient_ratio || '-' }}</template>
        </el-table-column>
        <el-table-column label="建议用量" width="140">
          <template #default="{ row }">
            {{ formatNumber(row.dose) }} {{ row.dose_unit_label }}
          </template>
        </el-table-column>
        <el-table-column label="施肥方式" width="100">
          <template #default="{ row }">{{ row.method_label || '-' }}</template>
        </el-table-column>
        <el-table-column prop="timing" label="施用时期" min-width="130">
          <template #default="{ row }">{{ row.timing || '-' }}</template>
        </el-table-column>
        <el-table-column label="已执行/累计实际用量" width="180">
          <template #default="{ row }">
            <span>{{ row.application_count || 0 }} 次</span>
            <span class="actual-total">
              / {{ formatNumber(row.actual_dose_total || 0) }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="comparisonItems.length > 1" class="comparison">
        <div class="section-title">同绿地历次检测对比</div>
        <el-table :data="comparisonItems" size="small" border>
          <el-table-column prop="sample_date" label="采样日期" width="110" fixed />
          <el-table-column prop="test_no" label="档案编号" width="140" fixed />
          <el-table-column prop="sample_point" label="采样点位" min-width="130" show-overflow-tooltip />
          <el-table-column v-for="indicator in indicatorCols" :key="indicator.key"
                           :label="indicator.label" min-width="110" align="center">
            <template #default="{ row }">
              <div class="compare-cell">
                <span>{{ formatNumber(row.values[indicator.key]) }}</span>
                <EnumTag v-if="row.grades[indicator.key]"
                         group="soil_grade" :value="row.grades[indicator.key]" />
                <span v-if="row.deltas[indicator.key] !== null && row.deltas[indicator.key] !== undefined"
                      class="delta" :class="deltaClass(row.deltas[indicator.key], indicator.key)">
                  {{ row.deltas[indicator.key] > 0 ? '▲' : '▼' }}{{ Math.abs(row.deltas[indicator.key]) }}
                </span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <template #footer>
      <el-button @click="close">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'

import { soilTestApi } from '@/api'
import EnumTag from '@/components/common/EnumTag.vue'
import { useMetaStore } from '@/stores/meta'
import { formatDate, formatNumber } from '@/utils/format'

const emit = defineEmits(['registerFert'])

const metaStore = useMetaStore()
const visible = ref(false)
const loading = ref(false)
const detail = ref({})
const comparison = ref({ items: [], indicators: [] })

const comparisonItems = computed(() => comparison.value.items || [])
const indicatorCols = computed(() => comparison.value.indicators || [])

const INDICATOR_LABEL_KEYS = ['ph', 'organic_matter', 'alkaline_n', 'available_p', 'available_k']

const indicatorRows = computed(() => {
  const currentIndex = comparisonItems.value.findIndex((item) => item.id === detail.value.id)
  return INDICATOR_LABEL_KEYS.map((key) => {
    const meta = metaStore.indicators.find((item) => item.key === key) || {}
    const current = comparisonItems.value[currentIndex]
    const previous = currentIndex > 0 ? comparisonItems.value[currentIndex - 1] : null
    return {
      key,
      label: meta.label || key,
      unit: meta.unit || '',
      value: detail.value[key],
      grade: detail.value.grades?.[key] ?? null,
      delta: current && previous ? current.deltas[key] : null,
    }
  })
})

function deltaClass(delta, key) {
  if (delta === null || delta === undefined || delta === 0) return 'delta-flat'
  // pH 偏离 7 视为变差；养分类整体上升视为改善，下降为不足
  if (key === 'ph') {
    const current = detail.value.ph
    if (current === null || current === undefined) return 'delta-flat'
    return Math.abs(current - 7) <= 0.5 ? 'delta-up' : 'delta-down'
  }
  return delta > 0 ? 'delta-up' : 'delta-down'
}

async function open(id) {
  visible.value = true
  loading.value = true
  detail.value = {}
  comparison.value = { items: [], indicators: [] }
  try {
    const data = await soilTestApi.detail(id)
    detail.value = data
    await metaStore.ensureIndicators()
    if (data.green_space_id) {
      comparison.value = await soilTestApi.comparison(data.green_space_id)
    }
  } finally {
    loading.value = false
  }
}

function close() {
  visible.value = false
}

defineExpose({ open })
</script>

<style scoped>
.section-title {
  font-weight: 600;
  font-size: 14px;
  margin: 16px 0 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.add-fert {
  margin-left: auto;
}

.unit {
  color: #909399;
  font-size: 12px;
}

.advice-box {
  margin-top: 12px;
  padding: 10px 12px;
  background: var(--gs-bg);
  border-radius: 6px;
  color: #606266;
  font-size: 13px;
  line-height: 1.7;
}

.actual-total {
  color: var(--gs-primary);
  margin-left: 4px;
}

.compare-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.delta {
  font-size: 11px;
}

.delta-up {
  color: #2f855a;
}

.delta-down {
  color: #e6a23c;
}

.delta-flat {
  color: #909399;
}
</style>

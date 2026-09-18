<template>
  <div class="page">
    <PageHeader title="土壤检测档案" description="登记采样信息与理化指标，结合绿地类型生成施肥配方，支撑后续施肥作业">
      <template #actions>
        <el-button type="primary" :icon="'Plus'" @click="formDialog.open()">登记土壤检测</el-button>
      </template>
    </PageHeader>

    <div class="panel">
      <div class="filter-bar">
        <el-input v-model="filters.keyword" placeholder="编号 / 点位 / 检测机构 / 报告编号" clearable
                  :prefix-icon="'Search'" @keyup.enter="search" @clear="search" />
        <div style="width: 220px">
          <GreenSpaceSelect v-model="filters.green_space_id" placeholder="按绿地筛选" @update:model-value="search" />
        </div>
        <el-select v-model="filters.soil_texture" placeholder="土壤质地" clearable @change="search">
          <el-option v-for="item in textureOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.nitrogen_level" placeholder="碱解氮水平" clearable @change="search">
          <el-option v-for="item in nutrientOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.ph_level" placeholder="酸碱度水平" clearable @change="search">
          <el-option v-for="item in phOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-date-picker v-model="dateRange" type="daterange" unlink-panels value-format="YYYY-MM-DD"
                        start-placeholder="采样日期起" end-placeholder="采样日期止" @change="onDateChange" />
        <el-button type="primary" :icon="'Search'" @click="search">查询</el-button>
        <el-button :icon="'RefreshLeft'" @click="reset">重置</el-button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard label="检测档案" :value="formatNumber(summary?.total_count ?? 0)" unit="份"
                :hint="`覆盖绿地 ${formatNumber(summary?.green_space_count ?? 0)} 处`" icon="Histogram" />
      <StatCard label="酸碱异常" :value="formatNumber(summary?.abnormal_ph_count ?? 0)" unit="份"
                hint="强酸、偏酸或偏碱，需调酸/压碱" tone="warning" icon="Sunny" />
      <StatCard label="有机质不足" :value="formatNumber(summary?.low_organic_count ?? 0)" unit="份"
                hint="有机质极低或偏低，建议增施有机肥" tone="warning" icon="Coffee" />
      <StatCard label="养分缺乏" :value="formatNumber(summary?.nutrient_deficient_count ?? 0)" unit="份"
                hint="氮/磷/钾至少一项缺乏或偏低" tone="danger" icon="Warning" />
      <StatCard label="配方已落地" :value="formatNumber(summary?.applied_test_count ?? 0)" unit="份"
                hint="已有回填实际用量的施肥作业" tone="info" icon="CircleCheck" />
    </div>

    <div class="panel">
      <div class="table-toolbar">
        <span class="summary-text">
          共 <strong>{{ meta.total }}</strong> 份检测档案，
          其中 <strong>{{ formatNumber(summary?.nutrient_deficient_count ?? 0) }}</strong> 份提示养分缺乏
        </span>
        <el-button :icon="'Refresh'" text @click="load">刷新</el-button>
      </div>

      <el-table :data="items" v-loading="loading" border stripe>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-detail">
              <span><b>采样深度：</b>{{ row.sample_depth != null ? `${row.sample_depth} cm` : '-' }}</span>
              <span><b>土壤质地：</b>{{ row.soil_texture_label || '-' }}</span>
              <span><b>检测机构：</b>{{ row.lab_org }}</span>
              <span><b>报告编号：</b>{{ row.report_no || '-' }}</span>
              <span><b>容重：</b>{{ row.bulk_density != null ? `${row.bulk_density} g/cm³` : '-' }}</span>
              <span><b>全盐量：</b>{{ row.salinity != null ? `${row.salinity} g/kg` : '-' }}</span>
              <span><b>含水率：</b>{{ row.moisture != null ? `${row.moisture}%` : '-' }}</span>
              <span><b>目标植物：</b>{{ row.target_plants || '-' }}</span>
              <span><b>登记时间：</b>{{ formatDateTime(row.created_at) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="test_no" label="档案编号" width="150" />
        <el-table-column label="所属绿地" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.green_space?.name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="sample_date" label="采样日期" width="105" />
        <el-table-column prop="sample_point" label="采样点位" min-width="150" show-overflow-tooltip />
        <el-table-column label="pH 酸碱度" width="115">
          <template #default="{ row }">
            <div>{{ formatNumber(row.ph_value) }}</div>
            <EnumTag group="ph_level" :value="row.ph_level" :label="row.ph_level_label" />
          </template>
        </el-table-column>
        <el-table-column label="有机质(g/kg)" width="120">
          <template #default="{ row }">
            <div>{{ formatNumber(row.organic_matter) }}</div>
            <EnumTag group="organic_level" :value="row.organic_level" :label="row.organic_level_label" />
          </template>
        </el-table-column>
        <el-table-column label="碱解氮" width="95" align="right">
          <template #default="{ row }">{{ formatNumber(row.alkali_nitrogen) }}</template>
        </el-table-column>
        <el-table-column label="有效磷" width="95" align="right">
          <template #default="{ row }">{{ formatNumber(row.available_phosphorus) }}</template>
        </el-table-column>
        <el-table-column label="速效钾" width="95" align="right">
          <template #default="{ row }">{{ formatNumber(row.available_potassium) }}</template>
        </el-table-column>
        <el-table-column label="推荐肥料" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <div>{{ row.fertilizer_name || '-' }}</div>
            <span class="cell-sub">{{ row.application_method_label || '' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="施肥作业" width="90" align="center">
          <template #default="{ row }">{{ row.application_count }} 次</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="detailDrawer.open(row.id)">档案/对比</el-button>
            <el-button link type="primary" @click="formDialog.open(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="meta.total"
        :current-page="meta.page"
        :page-size="meta.page_size"
        :page-sizes="[10, 20, 50]"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <SoilTestFormDialog ref="formDialog" @saved="load" />
    <SoilTestDetailDrawer ref="detailDrawer" @changed="load" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { soilTestApi } from '@/api'
import EnumTag from '@/components/common/EnumTag.vue'
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { useListQuery } from '@/composables/useListQuery'
import { formatDateTime, formatNumber } from '@/utils/format'

import SoilTestFormDialog from './SoilTestFormDialog.vue'
import SoilTestDetailDrawer from './SoilTestDetailDrawer.vue'

const route = useRoute()
const formDialog = ref(null)
const detailDrawer = ref(null)
const dateRange = ref([])

const { options: textureOptions } = useEnumOptions('soil_texture')
const { options: nutrientOptions } = useEnumOptions('nutrient_level')
const { options: phOptions } = useEnumOptions('ph_level')

const { filters, meta, items, summary, loading, load, search, resetFilters, handlePageChange, handleSizeChange } =
  useListQuery(soilTestApi.list, {
    initialFilters: {
      keyword: '',
      green_space_id: route.query.green_space_id ? Number(route.query.green_space_id) : null,
      soil_texture: '',
      nitrogen_level: '',
      ph_level: '',
      date_from: '',
      date_to: '',
    },
  })

function onDateChange(value) {
  filters.date_from = value?.[0] || ''
  filters.date_to = value?.[1] || ''
  search()
}

function reset() {
  dateRange.value = []
  resetFilters()
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除土壤检测档案「${row.test_no}」吗？其关联的施肥作业将一并删除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
    await soilTestApi.remove(row.id)
    ElMessage.success('土壤检测档案已删除')
    await load()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.cell-sub {
  color: #909399;
  font-size: 12px;
}

.expand-detail {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 6px 16px;
  padding: 4px 12px;
  color: #606266;
  font-size: 13px;
}
</style>

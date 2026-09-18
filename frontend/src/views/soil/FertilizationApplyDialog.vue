<template>
  <el-dialog :model-value="visible"
             :title="isEdit ? `回填施肥作业 · ${form.application_no}` : `登记施肥作业 · 引用 ${testNo}`"
             width="720px" top="8vh" destroy-on-close @update:model-value="close">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="130px">
      <el-alert v-if="formula" type="info" :closable="false" class="formula-alert">
        <template #title>
          引用配方：{{ formula.fertilizer_name || '-' }}
          （{{ formula.fertilizer_type_label || '-' }}），
          建议 {{ formatNumber(formula.dosage_per_sqm) }} kg/㎡，{{ formula.application_method_label || '' }}，
          {{ formula.application_frequency || '-' }}
        </template>
      </el-alert>

      <el-divider content-position="left">计划安排</el-divider>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="计划施肥日期" prop="plan_date" :error="fieldErrors.plan_date">
            <el-date-picker v-model="form.plan_date" type="date" value-format="YYYY-MM-DD"
                            placeholder="选择日期" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="执行班组" :error="fieldErrors.executor">
            <el-input v-model="form.executor" placeholder="如：绿化二班" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="肥料名称" :error="fieldErrors.fertilizer_name">
            <el-input v-model="form.fertilizer_name" placeholder="默认带出配方肥料" maxlength="96" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="施肥方式" :error="fieldErrors.application_method">
            <el-select v-model="form.application_method" clearable placeholder="请选择" style="width: 100%">
              <el-option v-for="item in methodOptions" :key="item.value" :label="item.label"
                         :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="计划单位用量" :error="fieldErrors.planned_dosage">
            <el-input-number v-model="form.planned_dosage" :min="0" :max="100" :precision="3"
                             :controls="false" style="width: 100%" />
            <span class="unit-text">kg/㎡</span>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="计划施肥面积" :error="fieldErrors.planned_area">
            <el-input-number v-model="form.planned_area" :min="0" :max="99999999" :precision="2"
                             :controls="false" style="width: 100%" />
            <span class="unit-text">㎡</span>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="计划总用量">
            <el-input :model-value="plannedTotalText" disabled />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">实际执行回填</el-divider>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="作业状态" prop="status">
            <el-select v-model="form.status" style="width: 100%">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label"
                         :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="实际施肥日期" :error="fieldErrors.applied_date">
            <el-date-picker v-model="form.applied_date" type="date" value-format="YYYY-MM-DD"
                            placeholder="回填实际作业日期" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="实际单位用量" :error="fieldErrors.actual_dosage">
            <el-input-number v-model="form.actual_dosage" :min="0" :max="100" :precision="3"
                             :controls="false" style="width: 100%" />
            <span class="unit-text">kg/㎡</span>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="实际施肥面积" :error="fieldErrors.actual_area">
            <el-input-number v-model="form.actual_area" :min="0" :max="99999999" :precision="2"
                             :controls="false" style="width: 100%" />
            <span class="unit-text">㎡</span>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="实际总用量">
            <el-input :model-value="actualTotalText" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="与计划偏差">
            <el-input :model-value="deviationText" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="作业人员" :error="fieldErrors.worker">
            <el-input v-model="form.worker" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="工时" :error="fieldErrors.work_hours">
            <el-input-number v-model="form.work_hours" :min="0" :max="1000" :precision="1"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="备注" :error="fieldErrors.remark">
        <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="2000" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fertilizationApi } from '@/api'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { formatNumber } from '@/utils/format'

const emit = defineEmits(['saved'])

const { options: methodOptions } = useEnumOptions('fertilization_method')
const { options: statusOptions } = useEnumOptions('application_status')

const formRef = ref(null)
const visible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const fieldErrors = ref({})
const formula = ref(null)
const form = reactive(emptyForm())

const isEdit = computed(() => editingId.value !== null)
const testNo = computed(() => formula.value?.test_no || '')

const rules = {
  plan_date: [{ required: true, message: '请选择计划施肥日期', trigger: 'change' }],
  status: [{ required: true, message: '请选择作业状态', trigger: 'change' }],
}

function emptyForm() {
  return {
    application_no: '',
    soil_test_id: null,
    plan_date: '',
    fertilizer_name: '',
    fertilizer_type: '',
    planned_dosage: null,
    planned_area: null,
    application_method: '',
    executor: '',
    status: 'planned',
    applied_date: '',
    actual_dosage: null,
    actual_area: null,
    worker: '',
    work_hours: null,
    remark: '',
  }
}

function toNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

const plannedTotal = computed(() => {
  const dosage = toNumber(form.planned_dosage)
  const area = toNumber(form.planned_area)
  return dosage !== null && area !== null ? dosage * area : null
})

const actualTotal = computed(() => {
  const dosage = toNumber(form.actual_dosage)
  const area = toNumber(form.actual_area)
  return dosage !== null && area !== null ? dosage * area : null
})

const plannedTotalText = computed(() =>
  plannedTotal.value === null ? '填写单位用量与面积后自动计算' : `${formatNumber(plannedTotal.value)} kg`,
)
const actualTotalText = computed(() =>
  actualTotal.value === null ? '回填后自动计算' : `${formatNumber(actualTotal.value)} kg`,
)
const deviationText = computed(() => {
  if (plannedTotal.value === null || actualTotal.value === null) return '回填实际用量后计算'
  const deviation = actualTotal.value - plannedTotal.value
  const sign = deviation > 0 ? '+' : ''
  return `${sign}${formatNumber(deviation)} kg`
})

function open(row = null, test = null) {
  Object.assign(form, emptyForm())
  fieldErrors.value = {}
  editingId.value = row?.id ?? null
  formula.value = test
  if (row) {
    Object.keys(form).forEach((key) => {
      if (row[key] !== undefined && row[key] !== null) form[key] = row[key]
    })
  } else if (test) {
    form.soil_test_id = test.id
    form.fertilizer_name = test.fertilizer_name || ''
    form.fertilizer_type = test.fertilizer_type || ''
    form.application_method = test.application_method || ''
    form.planned_dosage = test.dosage_per_sqm ?? null
  }
  visible.value = true
}

function close() {
  visible.value = false
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  fieldErrors.value = {}
  const payload = { ...form }
  if (!payload.application_no) delete payload.application_no
  ;['fertilizer_type', 'application_method', 'applied_date'].forEach((key) => {
    if (!payload[key]) payload[key] = null
  })
  try {
    if (isEdit.value) {
      await fertilizationApi.update(editingId.value, payload)
      ElMessage.success('施肥作业已更新')
    } else {
      await fertilizationApi.create(payload)
      ElMessage.success('施肥作业登记成功')
    }
    emit('saved')
    close()
  } catch (error) {
    fieldErrors.value = error?.details || {}
  } finally {
    submitting.value = false
  }
}

defineExpose({ open })
</script>

<style scoped>
.formula-alert {
  margin-bottom: 12px;
}

.unit-text {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}
</style>

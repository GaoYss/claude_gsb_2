<template>
  <el-dialog :model-value="visible"
             :title="isEdit ? `编辑施肥作业 · ${form.fert_no}` : '登记施肥作业'"
             width="760px" top="6vh" destroy-on-close @update:model-value="close">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
      <el-form-item label="所属绿地" prop="green_space_id" :error="fieldErrors.green_space_id">
        <GreenSpaceSelect v-model="form.green_space_id" :preset="spacePreset"
                          @update:model-value="onGreenSpaceChange" />
      </el-form-item>
      <el-form-item label="引用施肥配方" :error="fieldErrors.formula_item_id">
        <el-select v-model="form.formula_item_id" filterable clearable placeholder="可选择最近检测档案给出的配方"
                   style="width: 100%" :loading="loadingOptions" @change="onFormulaChange">
          <el-option-group v-for="test in formulaOptions" :key="test.id"
                           :label="`${test.test_no}（${test.sample_date} ${test.sample_point}）`">
            <el-option v-for="item in test.formula_items" :key="item.id"
                       :label="`${item.product_name} · 建议 ${formatNumber(item.dose)} ${item.dose_unit_label}`"
                       :value="item.id">
              <span>{{ item.product_name }}</span>
              <span class="option-extra">
                {{ formatNumber(item.dose) }} {{ item.dose_unit_label }}
                <template v-if="item.method_label"> · {{ item.method_label }}</template>
              </span>
            </el-option>
          </el-option-group>
        </el-select>
        <div class="form-hint">选择配方后自动带出肥料名称与建议用量，并回填到该检测档案的配方执行情况中。</div>
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="肥料名称" prop="product_name" :error="fieldErrors.product_name">
            <el-input v-model="form.product_name" placeholder="如：氮磷钾复合肥" maxlength="96" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="施肥方式" :error="fieldErrors.method">
            <el-select v-model="form.method" clearable placeholder="请选择" style="width: 100%">
              <el-option v-for="item in methodOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="建议用量" :error="fieldErrors.planned_dose">
            <el-input-number v-model="form.planned_dose" :min="0" :precision="2" :controls="false"
                             placeholder="配方建议用量" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="建议单位" :error="fieldErrors.planned_unit">
            <el-select v-model="form.planned_unit" clearable placeholder="单位" style="width: 100%">
              <el-option v-for="item in doseUnitOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="实际用量" prop="actual_dose" :error="fieldErrors.actual_dose">
            <el-input-number v-model="form.actual_dose" :min="0" :precision="2" :controls="false"
                             placeholder="本次实际施用用量" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="用量单位" :error="fieldErrors.actual_unit">
            <el-select v-model="form.actual_unit" style="width: 100%">
              <el-option v-for="item in doseUnitOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="施肥日期" prop="fert_date" :error="fieldErrors.fert_date">
            <el-date-picker v-model="form.fert_date" type="date" value-format="YYYY-MM-DD"
                            placeholder="选择日期" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="施肥人员" :error="fieldErrors.operator">
            <el-input v-model="form.operator" placeholder="如：赵春生" maxlength="64" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="关联养护记录" :error="fieldErrors.maintenance_record_id">
        <RecordSelect v-model="form.maintenance_record_id" :green-space-id="form.green_space_id"
                      :preset="recordPreset" />
      </el-form-item>
      <el-form-item label="备注" :error="fieldErrors.remark">
        <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="2000"
                  placeholder="如：施肥后浇透水、天气情况等" />
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

import { fertilizationApi, soilTestApi } from '@/api'
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import RecordSelect from '@/components/common/RecordSelect.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { formatNumber, today } from '@/utils/format'

const emit = defineEmits(['saved'])

const { options: methodOptions } = useEnumOptions('fert_method')
const { options: doseUnitOptions } = useEnumOptions('fert_dose_unit')

const formRef = ref(null)
const visible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const loadingOptions = ref(false)
const fieldErrors = ref({})
const spacePreset = ref(null)
const recordPreset = ref(null)
const formulaOptions = ref([])
const form = reactive(emptyForm())

const isEdit = computed(() => editingId.value !== null)

const rules = {
  green_space_id: [{ required: true, message: '请选择所属绿地', trigger: 'change' }],
  product_name: [{ required: true, message: '请填写肥料名称或选择配方', trigger: 'blur' }],
  actual_dose: [{ required: true, message: '请填写实际用量', trigger: 'blur' }],
  fert_date: [{ required: true, message: '请选择施肥日期', trigger: 'change' }],
}

function emptyForm() {
  return {
    fert_no: '',
    green_space_id: null,
    soil_test_id: null,
    formula_item_id: null,
    maintenance_record_id: null,
    product_name: '',
    planned_dose: null,
    planned_unit: '',
    actual_dose: null,
    actual_unit: 'kg_per_mu',
    method: '',
    fert_date: today(),
    operator: '',
    remark: '',
  }
}

async function open(row = null, preset = {}) {
  Object.assign(form, emptyForm())
  fieldErrors.value = {}
  spacePreset.value = null
  recordPreset.value = null
  formulaOptions.value = []
  editingId.value = row?.id ?? null
  if (row) {
    // 列表行不含备注等明细字段，编辑前拉取详情避免回填时清空
    let full = row
    if (row.remark === undefined) {
      try {
        full = await fertilizationApi.detail(row.id)
      } catch {
        full = row
      }
    }
    Object.keys(form).forEach((key) => {
      if (full[key] !== undefined && full[key] !== null) form[key] = full[key]
    })
    spacePreset.value = full.green_space || null
    recordPreset.value = full.record ? { ...full.record, id: full.maintenance_record_id } : null
  }
  // 从检测详情「登记施肥作业」进入时预置绿地与配方
  if (preset.green_space) {
    form.green_space_id = preset.green_space.id
    spacePreset.value = preset.green_space
  }
  if (form.green_space_id) await loadFormulaOptions(form.green_space_id)
  if (preset.formulaItemId) {
    form.formula_item_id = preset.formulaItemId
    onFormulaChange(preset.formulaItemId)
  }
  visible.value = true
}

function close() {
  visible.value = false
}

async function onGreenSpaceChange(spaceId) {
  form.formula_item_id = null
  form.soil_test_id = null
  form.maintenance_record_id = null
  recordPreset.value = null
  formulaOptions.value = []
  if (spaceId) await loadFormulaOptions(spaceId)
}

async function loadFormulaOptions(spaceId) {
  loadingOptions.value = true
  try {
    const data = await soilTestApi.formulaOptions(spaceId)
    formulaOptions.value = data?.items || []
  } finally {
    loadingOptions.value = false
  }
}

function findFormulaItem(itemId) {
  for (const test of formulaOptions.value) {
    const found = (test.formula_items || []).find((item) => item.id === itemId)
    if (found) return { test, item: found }
  }
  return null
}

function onFormulaChange(itemId) {
  if (!itemId) return
  const found = findFormulaItem(itemId)
  if (!found) return
  const { test, item } = found
  form.soil_test_id = test.id
  form.product_name = item.product_name
  form.planned_dose = item.dose
  form.planned_unit = item.dose_unit
  if (item.method) form.method = item.method
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  fieldErrors.value = {}
  const payload = { ...form }
  if (!payload.fert_no) delete payload.fert_no
  for (const key of ['soil_test_id', 'formula_item_id', 'maintenance_record_id',
                     'planned_dose', 'planned_unit', 'method']) {
    if (payload[key] === '' ) payload[key] = null
  }
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
.option-extra {
  color: #909399;
  font-size: 12px;
  margin-left: 10px;
}
</style>

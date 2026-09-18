<template>
  <el-dialog :model-value="visible"
             :title="isEdit ? `编辑土壤检测档案 · ${form.test_no}` : '登记土壤检测档案'"
             width="860px" top="4vh" destroy-on-close @update:model-value="close">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
      <div class="section-title">采样登记</div>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="所属绿地" prop="green_space_id" :error="fieldErrors.green_space_id">
            <GreenSpaceSelect v-model="form.green_space_id" :preset="spacePreset" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="采样日期" prop="sample_date" :error="fieldErrors.sample_date">
            <el-date-picker v-model="form.sample_date" type="date" value-format="YYYY-MM-DD"
                            placeholder="选择采样日期" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="采样点位" prop="sample_point" :error="fieldErrors.sample_point">
            <el-input v-model="form.sample_point" placeholder="如：中心草坪东南角" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="采样深度(cm)" :error="fieldErrors.sample_depth">
            <el-input-number v-model="form.sample_depth" :min="0" :max="500" :precision="1"
                             :controls="false" placeholder="如：20" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="检测机构" prop="lab" :error="fieldErrors.lab">
            <el-input v-model="form.lab" placeholder="如：市园林质检中心" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="报告编号" :error="fieldErrors.lab_report_no">
            <el-input v-model="form.lab_report_no" placeholder="检测机构出具的报告编号" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="土壤质地" :error="fieldErrors.texture">
            <el-select v-model="form.texture" clearable placeholder="请选择" style="width: 100%">
              <el-option v-for="item in textureOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <div class="section-title">检测结果</div>
      <el-row :gutter="16">
        <el-col v-for="indicator in indicators" :key="indicator.key" :span="12">
          <el-form-item :label="indicator.label" :error="fieldErrors[indicator.key]">
            <div class="indicator-field">
              <el-input-number
                v-model="form[indicator.key]"
                :min="indicator.key === 'ph' ? 3 : 0"
                :max="indicator.key === 'ph' ? 10 : undefined"
                :precision="2"
                :controls="false"
                :placeholder="indicator.unit ? `单位 ${indicator.unit}` : '无量纲'"
                style="flex: 1"
              />
              <EnumTag v-if="grades[indicator.key]"
                       group="soil_grade" :value="grades[indicator.key]" />
              <span v-else class="grade-placeholder">{{ indicator.unit || '—' }}</span>
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <div class="section-title">施肥配方建议</div>
      <el-form-item label="目标作物" :error="fieldErrors.target_crop">
        <el-input v-model="form.target_crop"
                  placeholder="结合绿地类型与主要植物，如：马尼拉草坪、香樟与红叶石楠"
                  maxlength="128" />
      </el-form-item>

      <el-form-item label="配方明细" :error="formulaError">
        <el-table :data="form.formula_items" size="small" border class="formula-table">
          <el-table-column label="肥料名称" min-width="150">
            <template #default="{ row }">
              <el-input v-model="row.product_name" placeholder="如：腐熟有机肥" maxlength="96" />
            </template>
          </el-table-column>
          <el-table-column label="养分配比" width="130">
            <template #default="{ row }">
              <el-input v-model="row.nutrient_ratio" placeholder="如 15-15-15" maxlength="32" />
            </template>
          </el-table-column>
          <el-table-column label="建议用量" width="150">
            <template #default="{ row }">
              <el-input-number v-model="row.dose" :min="0" :precision="2" :controls="false"
                               placeholder="用量" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="140">
            <template #default="{ row }">
              <el-select v-model="row.dose_unit" style="width: 100%">
                <el-option v-for="item in doseUnitOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="施肥方式" width="130">
            <template #default="{ row }">
              <el-select v-model="row.method" clearable placeholder="选择" style="width: 100%">
                <el-option v-for="item in methodOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="施用时期" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.timing" placeholder="如：春季返青前" maxlength="96" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" align="center">
            <template #default="{ $index }">
              <el-button link type="danger" :icon="'Delete'" @click="removeItem($index)" />
            </template>
          </el-table-column>
        </el-table>
        <el-button class="add-formula" :icon="'Plus'" plain size="small" @click="addItem">
          添加配方肥料
        </el-button>
      </el-form-item>

      <el-form-item label="施肥建议" :error="fieldErrors.fert_advice">
        <el-input v-model="form.fert_advice" type="textarea" :rows="3" maxlength="4000"
                  placeholder="留空将根据酸碱度、有机质与氮磷钾丰缺等级，结合目标作物自动生成建议" />
      </el-form-item>
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

import { soilTestApi } from '@/api'
import EnumTag from '@/components/common/EnumTag.vue'
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { useMetaStore } from '@/stores/meta'
import { today } from '@/utils/format'

const emit = defineEmits(['saved'])

const { options: textureOptions } = useEnumOptions('soil_texture')
const { options: doseUnitOptions } = useEnumOptions('fert_dose_unit')
const { options: methodOptions } = useEnumOptions('fert_method')
const metaStore = useMetaStore()

const formRef = ref(null)
const visible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const fieldErrors = ref({})
const spacePreset = ref(null)
const form = reactive(emptyForm())

const isEdit = computed(() => editingId.value !== null)
const indicators = computed(() => metaStore.indicators)

// 配方明细的校验错误（后端按下标返回）统一汇总展示
const formulaError = computed(() => {
  const entries = Object.entries(fieldErrors.value).filter(([key]) => key.startsWith('formula_items'))
  if (!entries.length) return ''
  const FIELD_LABELS = {
    product_name: '肥料名称',
    dose: '建议用量',
    dose_unit: '用量单位',
    method: '施肥方式',
  }
  return entries
    .map(([key, message]) => {
      const match = key.match(/formula_items(?:\.(\d+))?(?:\.(\w+))?/)
      if (!match) return message
      const row = match[1] !== undefined ? `第 ${Number(match[1]) + 1} 行` : ''
      const field = FIELD_LABELS[match[2]] || ''
      return `${row}${field ? ` ${field}` : ''}：${message}`
    })
    .join('；')
})
const grades = computed(() => {
  const result = {}
  for (const indicator of metaStore.indicators) {
    result[indicator.key] = metaStore.gradeOf(indicator.key, form[indicator.key])
  }
  return result
})

const rules = {
  green_space_id: [{ required: true, message: '请选择所属绿地', trigger: 'change' }],
  sample_date: [{ required: true, message: '请选择采样日期', trigger: 'change' }],
  sample_point: [{ required: true, message: '请输入采样点位', trigger: 'blur' }],
  lab: [{ required: true, message: '请输入检测机构', trigger: 'blur' }],
}

function emptyForm() {
  return {
    test_no: '',
    green_space_id: null,
    sample_date: today(),
    sample_point: '',
    sample_depth: null,
    lab: '',
    lab_report_no: '',
    texture: '',
    ph: null,
    organic_matter: null,
    alkaline_n: null,
    available_p: null,
    available_k: null,
    target_crop: '',
    fert_advice: '',
    remark: '',
    formula_items: [],
  }
}

function emptyItem() {
  return {
    product_name: '',
    nutrient_ratio: '',
    dose: null,
    dose_unit: 'kg_per_mu',
    method: '',
    timing: '',
  }
}

function addItem() {
  form.formula_items.push(emptyItem())
}

function removeItem(index) {
  form.formula_items.splice(index, 1)
}

async function open(row = null) {
  Object.assign(form, emptyForm())
  fieldErrors.value = {}
  spacePreset.value = null
  editingId.value = row?.id ?? null
  await metaStore.ensureIndicators()
  if (row) {
    // 列表行不含配方明细，编辑前拉取详情
    const detail = await soilTestApi.detail(row.id)
    Object.keys(form).forEach((key) => {
      if (detail[key] !== undefined && detail[key] !== null) form[key] = detail[key]
    })
    form.formula_items = (detail.formula_items || []).map((item) => ({
      id: item.id,
      product_name: item.product_name,
      nutrient_ratio: item.nutrient_ratio || '',
      dose: item.dose,
      dose_unit: item.dose_unit,
      method: item.method || '',
      timing: item.timing || '',
    }))
    spacePreset.value = detail.green_space || null
  }
  visible.value = true
}

function close() {
  visible.value = false
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  const invalidItem = form.formula_items.find((item) => !item.product_name?.trim())
  if (invalidItem) {
    fieldErrors.value = { formula_items: '存在未填写肥料名称的配方行，请补全或删除' }
    return
  }
  submitting.value = true
  fieldErrors.value = {}
  const payload = JSON.parse(JSON.stringify(form))
  if (!payload.test_no) delete payload.test_no
  payload.formula_items = payload.formula_items.map((item) => ({
    ...item,
    method: item.method || null,
    nutrient_ratio: item.nutrient_ratio || null,
    timing: item.timing || null,
    dose: item.dose ?? null,
  }))
  try {
    if (isEdit.value) {
      await soilTestApi.update(editingId.value, payload)
      ElMessage.success('土壤检测档案已更新')
    } else {
      await soilTestApi.create(payload)
      ElMessage.success('土壤检测档案登记成功')
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
.section-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--gs-primary);
  margin: 4px 0 14px;
  padding-left: 8px;
  border-left: 3px solid var(--gs-primary-light);
}

.indicator-field {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.grade-placeholder {
  color: #c0c4cc;
  font-size: 12px;
  min-width: 32px;
}

.formula-table {
  margin-bottom: 8px;
}

.add-formula {
  width: 100%;
  border-style: dashed;
}
</style>

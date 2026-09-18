<template>
  <el-dialog :model-value="visible"
             :title="isEdit ? `编辑土壤检测档案 · ${form.test_no}` : '登记土壤检测档案'"
             width="860px" top="5vh" destroy-on-close @update:model-value="close">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
      <el-divider content-position="left">采样与检测信息</el-divider>
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
            <el-input v-model="form.sample_point" placeholder="如：中央草坪 5 点混合样" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="采样深度(cm)" :error="fieldErrors.sample_depth">
            <el-input-number v-model="form.sample_depth" :min="0" :max="500" :precision="1"
                             :controls="false" placeholder="如：20" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="检测机构" prop="lab_org" :error="fieldErrors.lab_org">
            <el-input v-model="form.lab_org" placeholder="如：市园林科学研究所检测中心" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="报告编号" :error="fieldErrors.report_no">
            <el-input v-model="form.report_no" placeholder="检测机构出具的报告编号" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="土壤质地" :error="fieldErrors.soil_texture">
            <el-select v-model="form.soil_texture" clearable placeholder="请选择" style="width: 100%">
              <el-option v-for="item in textureOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目标作物/植物" :error="fieldErrors.target_plants">
            <el-input v-model="form.target_plants" placeholder="如：马尼拉草坪、金森女贞" maxlength="255" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">理化检测指标</el-divider>
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="酸碱度 pH" prop="ph_value" :error="fieldErrors.ph_value">
            <el-input-number v-model="form.ph_value" :min="2" :max="12" :precision="2"
                             :controls="false" placeholder="如：6.8" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="有机质(g/kg)" prop="organic_matter" :error="fieldErrors.organic_matter">
            <el-input-number v-model="form.organic_matter" :min="0" :max="1000" :precision="2"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="容重(g/cm³)" :error="fieldErrors.bulk_density">
            <el-input-number v-model="form.bulk_density" :min="0.1" :max="3" :precision="2"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="碱解氮(mg/kg)" prop="alkali_nitrogen" :error="fieldErrors.alkali_nitrogen">
            <el-input-number v-model="form.alkali_nitrogen" :min="0" :max="5000" :precision="2"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="有效磷(mg/kg)" prop="available_phosphorus"
                        :error="fieldErrors.available_phosphorus">
            <el-input-number v-model="form.available_phosphorus" :min="0" :max="5000" :precision="2"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="速效钾(mg/kg)" prop="available_potassium"
                        :error="fieldErrors.available_potassium">
            <el-input-number v-model="form.available_potassium" :min="0" :max="5000" :precision="2"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="全盐量(g/kg)" :error="fieldErrors.salinity">
            <el-input-number v-model="form.salinity" :min="0" :max="100" :precision="3"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="含水率(%)" :error="fieldErrors.moisture">
            <el-input-number v-model="form.moisture" :min="0" :max="100" :precision="2"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">
        <span class="divider-text">施肥配方</span>
        <span class="divider-hint">（留空由系统按检测结果与绿地类型自动生成，也可手工指定）</span>
      </el-divider>
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="肥料类型" :error="fieldErrors.fertilizer_type">
            <el-select v-model="form.fertilizer_type" clearable placeholder="留空自动生成" style="width: 100%">
              <el-option v-for="item in fertilizerTypeOptions" :key="item.value" :label="item.label"
                         :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="肥料名称" :error="fieldErrors.fertilizer_name">
            <el-input v-model="form.fertilizer_name" placeholder="如：三元复合肥" maxlength="96" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="养分配比" :error="fieldErrors.nutrient_ratio">
            <el-input v-model="form.nutrient_ratio" placeholder="如：15-15-15" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="建议用量(kg/㎡)" :error="fieldErrors.dosage_per_sqm">
            <el-input-number v-model="form.dosage_per_sqm" :min="0" :max="100" :precision="3"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="施肥方式" :error="fieldErrors.application_method">
            <el-select v-model="form.application_method" clearable placeholder="留空自动生成"
                       style="width: 100%">
              <el-option v-for="item in methodOptions" :key="item.value" :label="item.label"
                         :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="施肥频次" :error="fieldErrors.application_frequency">
            <el-input v-model="form.application_frequency" placeholder="如：每年 2-3 次" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="施肥时期" :error="fieldErrors.application_period">
            <el-input v-model="form.application_period" placeholder="如：春季返青前及秋季生长末期"
                      maxlength="128" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="配方说明" :error="fieldErrors.formula_advice">
        <el-input v-model="form.formula_advice" type="textarea" :rows="2" maxlength="2000"
                  placeholder="缺素矫正、改土与施肥注意事项；留空自动生成" />
      </el-form-item>

      <el-form-item label="检测结论" :error="fieldErrors.conclusion">
        <el-input v-model="form.conclusion" type="textarea" :rows="2" maxlength="2000" />
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="登记人" :error="fieldErrors.operator">
            <el-input v-model="form.operator" maxlength="64" />
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

import { soilTestApi } from '@/api'
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'

const emit = defineEmits(['saved'])

const { options: textureOptions } = useEnumOptions('soil_texture')
const { options: fertilizerTypeOptions } = useEnumOptions('fertilizer_type')
const { options: methodOptions } = useEnumOptions('fertilization_method')

const formRef = ref(null)
const visible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const fieldErrors = ref({})
const spacePreset = ref(null)
const form = reactive(emptyForm())

const isEdit = computed(() => editingId.value !== null)

const rules = {
  green_space_id: [{ required: true, message: '请选择所属绿地', trigger: 'change' }],
  sample_date: [{ required: true, message: '请选择采样日期', trigger: 'change' }],
  sample_point: [{ required: true, message: '请输入采样点位', trigger: 'blur' }],
  lab_org: [{ required: true, message: '请输入检测机构', trigger: 'blur' }],
  ph_value: [{ required: true, message: '请输入酸碱度 pH', trigger: 'blur' }],
  organic_matter: [{ required: true, message: '请输入有机质含量', trigger: 'blur' }],
  alkali_nitrogen: [{ required: true, message: '请输入碱解氮', trigger: 'blur' }],
  available_phosphorus: [{ required: true, message: '请输入有效磷', trigger: 'blur' }],
  available_potassium: [{ required: true, message: '请输入速效钾', trigger: 'blur' }],
}

function emptyForm() {
  return {
    test_no: '',
    green_space_id: null,
    sample_date: '',
    sample_point: '',
    sample_depth: null,
    lab_org: '',
    report_no: '',
    soil_texture: '',
    ph_value: null,
    organic_matter: null,
    alkali_nitrogen: null,
    available_phosphorus: null,
    available_potassium: null,
    bulk_density: null,
    salinity: null,
    moisture: null,
    target_plants: '',
    fertilizer_type: '',
    fertilizer_name: '',
    nutrient_ratio: '',
    dosage_per_sqm: null,
    application_frequency: '',
    application_method: '',
    application_period: '',
    formula_advice: '',
    conclusion: '',
    operator: '',
    remark: '',
  }
}

function open(row = null, preselect = null) {
  Object.assign(form, emptyForm())
  fieldErrors.value = {}
  spacePreset.value = null
  editingId.value = row?.id ?? null
  if (row) {
    Object.keys(form).forEach((key) => {
      if (row[key] !== undefined && row[key] !== null) form[key] = row[key]
    })
    spacePreset.value = row.green_space || null
  } else if (preselect?.greenSpaceId) {
    form.green_space_id = preselect.greenSpaceId
    spacePreset.value = preselect.preset || null
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
  if (!payload.test_no) delete payload.test_no
  // 空字符串的枚举/文本字段统一转为 null，便于后端判定是否自动生成配方
  ;['soil_texture', 'fertilizer_type', 'application_method'].forEach((key) => {
    if (!payload[key]) payload[key] = null
  })
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
.divider-text {
  font-weight: 600;
}

.divider-hint {
  color: #909399;
  font-size: 12px;
  font-weight: 400;
  margin-left: 6px;
}
</style>

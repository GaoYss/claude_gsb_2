"""土壤检测档案校验规则。"""

from ..constants import (
    FERTILIZATION_METHOD,
    FERTILIZER_TYPE,
    SOIL_TEXTURE,
)
from .common import PayloadValidator


def validate_soil_test(payload):
    validator = (
        PayloadValidator(payload)
        .integer("green_space_id", "所属绿地", required=True, min_value=1)
        .date("sample_date", "采样日期", required=True)
        .string("sample_point", "采样点位", required=True, max_length=128)
        .number("sample_depth", "采样深度(cm)", min_value=0, max_value=500, digits=1)
        .string("lab_org", "检测机构", required=True, max_length=128)
        .string("report_no", "检测报告编号", max_length=64)
        .enum("soil_texture", "土壤质地", group=SOIL_TEXTURE)
        # 理化指标
        .number("ph_value", "酸碱度 pH", required=True, min_value=2, max_value=12, digits=2)
        .number("organic_matter", "有机质(g/kg)", required=True, min_value=0, max_value=1000, digits=2)
        .number("alkali_nitrogen", "碱解氮(mg/kg)", required=True, min_value=0, max_value=5000, digits=2)
        .number("available_phosphorus", "有效磷(mg/kg)", required=True, min_value=0, max_value=5000, digits=2)
        .number("available_potassium", "速效钾(mg/kg)", required=True, min_value=0, max_value=5000, digits=2)
        .number("bulk_density", "土壤容重(g/cm³)", min_value=0.1, max_value=3, digits=2)
        .number("salinity", "全盐量(g/kg)", min_value=0, max_value=100, digits=3)
        .number("moisture", "土壤含水率(%)", min_value=0, max_value=100, digits=2)
        # 目标植物与施肥配方（留空由系统按检测结果自动生成，可手工调整）
        .string("target_plants", "目标作物/植物", max_length=255)
        .enum("fertilizer_type", "肥料类型", group=FERTILIZER_TYPE)
        .string("fertilizer_name", "肥料名称", max_length=96)
        .string("nutrient_ratio", "养分配比", max_length=64)
        .number("dosage_per_sqm", "建议用量(kg/㎡)", min_value=0, max_value=100, digits=3)
        .string("application_frequency", "施肥频次", max_length=64)
        .enum("application_method", "施肥方式", group=FERTILIZATION_METHOD)
        .string("application_period", "施肥时期", max_length=128)
        .text("formula_advice", "配方说明", max_length=2000)
        .text("conclusion", "检测结论", max_length=2000)
        .string("operator", "登记人", max_length=64)
        .text("remark", "备注", max_length=2000)
    )
    return validator.done()

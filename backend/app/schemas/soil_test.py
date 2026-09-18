"""土壤检测档案与施肥作业的校验规则。"""

from ..constants import FERT_DOSE_UNIT, FERT_METHOD, SOIL_TEXTURE
from ..utils.soil import INDICATOR_DEFS
from .common import PayloadValidator

# 各检测指标的取值范围，明显越界的数据直接拒绝。
INDICATOR_BOUNDS = {
    "ph": (3.0, 10.0),
    "organic_matter": (0, 500),
    "alkaline_n": (0, 5000),
    "available_p": (0, 1000),
    "available_k": (0, 2000),
}


def validate_soil_test(payload):
    validator = (
        PayloadValidator(payload)
        .integer("green_space_id", "所属绿地", required=True, min_value=1)
        .date("sample_date", "采样日期", required=True)
        .string("sample_point", "采样点位", required=True, max_length=128)
        .number("sample_depth", "采样深度", min_value=0, max_value=500)
        .string("lab", "检测机构", required=True, max_length=128)
        .string("lab_report_no", "检测报告编号", max_length=64)
        .enum("texture", "土壤质地", group=SOIL_TEXTURE)
        .number("ph", "酸碱度", min_value=3.0, max_value=10.0, digits=2)
        .number("organic_matter", "有机质", min_value=0, max_value=500)
        .number("alkaline_n", "碱解氮", min_value=0, max_value=5000)
        .number("available_p", "有效磷", min_value=0, max_value=1000)
        .number("available_k", "速效钾", min_value=0, max_value=2000)
        .string("target_crop", "目标作物", max_length=128)
        .text("fert_advice", "施肥建议", max_length=4000)
        .text("remark", "备注", max_length=2000)
    )
    data = validator.done()
    if "formula_items" in payload:
        data["formula_items"] = validate_formula_items(payload["formula_items"])
    return data


def validate_formula_items(raw_items):
    """校验嵌套的施肥配方明细，错误按下标定位。"""

    from decimal import Decimal, InvalidOperation

    from ..errors import ValidationError

    if raw_items is None:
        return []
    if not isinstance(raw_items, list):
        raise ValidationError("提交的数据未通过校验",
                              details={"formula_items": "施肥配方必须是明细列表"})
    if len(raw_items) > 20:
        raise ValidationError("提交的数据未通过校验",
                              details={"formula_items": "单次检测的配方明细不能超过 20 条"})

    items = []
    errors = {}
    for index, raw in enumerate(raw_items):
        prefix = f"formula_items.{index}"
        if not isinstance(raw, dict):
            errors[prefix] = "配方明细必须是对象"
            continue

        product_name = (str(raw.get("product_name") or "")).strip()
        if not product_name:
            errors[f"{prefix}.product_name"] = "肥料名称不能为空"
        elif len(product_name) > 96:
            errors[f"{prefix}.product_name"] = "肥料名称长度不能超过 96 个字符"

        dose_unit = str(raw.get("dose_unit") or "kg_per_mu").strip()
        if not FERT_DOSE_UNIT.has(dose_unit):
            errors[f"{prefix}.dose_unit"] = "用量单位取值不合法"

        method = raw.get("method")
        if method not in (None, ""):
            method = str(method).strip()
            if not FERT_METHOD.has(method):
                errors[f"{prefix}.method"] = "施肥方式取值不合法"
        else:
            method = None

        dose = None
        raw_dose = raw.get("dose")
        if raw_dose not in (None, ""):
            try:
                dose = Decimal(str(raw_dose)).quantize(Decimal("0.01"))
            except (InvalidOperation, ValueError):
                errors[f"{prefix}.dose"] = "建议用量必须是数字"
            else:
                if dose < 0 or dose > Decimal("999999"):
                    errors[f"{prefix}.dose"] = "建议用量需在 0 ~ 999999 之间"

        nutrient_ratio = _bounded_text(raw.get("nutrient_ratio"), 32)
        timing = _bounded_text(raw.get("timing"), 96)

        items.append({
            "id": raw.get("id") if isinstance(raw.get("id"), int) else None,
            "product_name": product_name,
            "nutrient_ratio": nutrient_ratio,
            "dose": dose,
            "dose_unit": dose_unit,
            "method": method,
            "timing": timing,
        })

    if errors:
        raise ValidationError("提交的数据未通过校验", details=errors)
    return items


def _bounded_text(value, max_length):
    if value is None:
        return None
    text = str(value).strip()
    return text[:max_length] or None


def validate_fertilization(payload):
    return (
        PayloadValidator(payload)
        .integer("green_space_id", "所属绿地", required=True, min_value=1)
        .integer("soil_test_id", "检测档案", min_value=1)
        .integer("formula_item_id", "施肥配方", min_value=1)
        .integer("maintenance_record_id", "关联养护记录", min_value=1)
        .string("product_name", "肥料名称", max_length=96)
        .number("planned_dose", "建议用量", min_value=0, max_value=999999)
        .enum("planned_unit", "建议用量单位", group=FERT_DOSE_UNIT)
        .number("actual_dose", "实际用量", required=True, min_value=0, max_value=999999)
        .enum("actual_unit", "实际用量单位", group=FERT_DOSE_UNIT, default="kg_per_mu")
        .enum("method", "施肥方式", group=FERT_METHOD)
        .date("fert_date", "施肥日期", required=True)
        .string("operator", "施肥人员", max_length=64)
        .text("remark", "备注", max_length=2000)
        .done()
    )

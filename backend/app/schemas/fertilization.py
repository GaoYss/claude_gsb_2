"""施肥作业校验规则。"""

from ..constants import APPLICATION_STATUS, FERTILIZATION_METHOD, FERTILIZER_TYPE
from .common import PayloadValidator


def validate_fertilization(payload):
    return (
        PayloadValidator(payload)
        .integer("soil_test_id", "引用配方（土壤检测）", required=True, min_value=1)
        .date("plan_date", "计划施肥日期", required=True)
        .enum("fertilizer_type", "肥料类型", group=FERTILIZER_TYPE)
        .string("fertilizer_name", "肥料名称", max_length=96)
        .number("planned_dosage", "计划单位用量(kg/㎡)", min_value=0, max_value=100, digits=3)
        .number("planned_area", "计划施肥面积(㎡)", min_value=0, max_value=99999999, digits=2)
        .number("planned_amount", "计划总用量(kg)", min_value=0, max_value=99999999, digits=2)
        .enum("application_method", "施肥方式", group=FERTILIZATION_METHOD)
        .string("executor", "执行班组", max_length=64)
        .enum("status", "作业状态", group=APPLICATION_STATUS, default="planned")
        .date("applied_date", "实际施肥日期")
        .number("actual_dosage", "实际单位用量(kg/㎡)", min_value=0, max_value=100, digits=3)
        .number("actual_area", "实际施肥面积(㎡)", min_value=0, max_value=99999999, digits=2)
        .number("actual_amount", "实际总用量(kg)", min_value=0, max_value=99999999, digits=2)
        .string("worker", "作业人员", max_length=64)
        .number("work_hours", "工时", min_value=0, max_value=1000, digits=1)
        .text("remark", "备注", max_length=2000)
        .done()
    )

"""土壤检测指标的元数据与丰缺评级。

分级阈值参考全国第二次土壤普查常用标准并按绿地养护场景做了五档归并：
极低 / 偏低 / 适中 / 偏高 / 过高，评级结果用于指导施肥配方与前后对比解读。
"""

from ..constants import SOIL_GRADE

# 每项指标：展示名、单位、从低到高的五档分界（小于分界归入该档，末档兜底）。
INDICATOR_DEFS = {
    "ph": {
        "label": "酸碱度 pH",
        "unit": "",
        "breakpoints": [5.5, 6.5, 7.5, 8.5],
        "advice": {
            "very_low": "土壤强酸性，建议撒施生石灰等碱性物料调节酸碱度",
            "low": "土壤偏酸，可适量施用草木灰或含钙肥料调酸",
            "medium": "酸碱度适中，维持现有管理",
            "high": "土壤偏碱，可增施腐殖质肥料、避免使用碱性肥料",
            "very_high": "土壤强碱性，建议施用硫磺粉或酸性肥料改良",
        },
    },
    "organic_matter": {
        "label": "有机质",
        "unit": "g/kg",
        "breakpoints": [10, 20, 30, 40],
        "advice": {
            "very_low": "有机质极度匮乏，应大量增施腐熟有机肥与农家肥",
            "low": "有机质偏低，增施有机肥、堆肥或覆盖秸秆培肥",
            "medium": "有机质适中，坚持有机肥与化肥配合施用",
            "high": "有机质丰富，可减少有机肥投入",
            "very_high": "有机质过高，核实检测数据并暂停有机肥",
        },
    },
    "alkaline_n": {
        "label": "碱解氮",
        "unit": "mg/kg",
        "breakpoints": [60, 90, 120, 150],
        "advice": {
            "very_low": "氮素严重不足，增加氮肥用量并少量多次追施",
            "low": "氮素偏低，适量增施氮肥",
            "medium": "氮素适中，按目标作物常规用量施用",
            "high": "氮素偏高，控制氮肥、增施磷钾肥",
            "very_high": "氮素过量，暂停氮肥以防徒长与污染",
        },
    },
    "available_p": {
        "label": "有效磷",
        "unit": "mg/kg",
        "breakpoints": [5, 10, 20, 40],
        "advice": {
            "very_low": "有效磷极度缺乏，增施过磷酸钙等磷肥作基肥",
            "low": "有效磷偏低，适量增施磷肥",
            "medium": "有效磷适中，维持常规施磷水平",
            "high": "有效磷偏高，减少磷肥投入",
            "very_high": "有效磷过量，暂停磷肥并注意均衡施肥",
        },
    },
    "available_k": {
        "label": "速效钾",
        "unit": "mg/kg",
        "breakpoints": [50, 100, 150, 200],
        "advice": {
            "very_low": "速效钾严重不足，增施硫酸钾或氯化钾等钾肥",
            "low": "速效钾偏低，适量增施钾肥",
            "medium": "速效钾适中，维持常规施钾水平",
            "high": "速效钾偏高，减少钾肥投入",
            "very_high": "速效钾过量，暂停钾肥并关注养分平衡",
        },
    },
}

GRADE_ORDER = SOIL_GRADE.values  # very_low → very_high


def grade_of(indicator, value):
    """按分界值把检测值映射为五档等级。"""

    definition = INDICATOR_DEFS[indicator]
    for index, bound in enumerate(definition["breakpoints"]):
        if value < bound:
            return GRADE_ORDER[index]
    return GRADE_ORDER[-1]


def indicator_meta():
    """供前端展示指标名称、单位与评级分界。"""

    return {
        key: {
            "key": key,
            "label": meta["label"],
            "unit": meta["unit"],
            "breakpoints": meta["breakpoints"],
        }
        for key, meta in INDICATOR_DEFS.items()
    }


def build_advice(grades, target_crop=None, green_type=None):
    """根据各指标等级生成施肥改土建议，登记时未填建议则自动带出。"""

    tips = []
    for key in ("ph", "organic_matter", "alkaline_n", "available_p", "available_k"):
        grade = grades.get(key)
        if grade and grade not in ("medium",):
            tips.append(INDICATOR_DEFS[key]["advice"][grade])
    if not tips:
        tips.append("各项指标总体适宜，按目标作物常规养护方案施肥即可")
    subjects = "、".join(item for item in (green_type, target_crop) if item)
    prefix = f"针对{subjects}：" if subjects else ""
    return prefix + "；".join(tips) + "。"

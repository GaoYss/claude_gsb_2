"""土壤理化指标分级与施肥配方建议。

分级阈值采用城市绿地/园林土壤常用口径，入库时由 service 统一计算并落库，
保证历史档案在阈值调整后仍能还原当次判定；to_dict 时同时给出文案。
"""

# ---------------------------------------------------------------- 分级阈值
PH_BANDS = [
    (5.0, "strong_acid"),
    (6.5, "acid"),
    (7.5, "neutral"),
    (8.5, "alkaline"),
]
ORGANIC_BANDS = [
    (10.0, "very_low"),
    (20.0, "low"),
    (40.0, "medium"),
]
NITROGEN_BANDS = [
    (60.0, "lack"),
    (100.0, "low"),
    (150.0, "medium"),
]
PHOSPHORUS_BANDS = [
    (5.0, "lack"),
    (15.0, "low"),
    (40.0, "medium"),
]
POTASSIUM_BANDS = [
    (50.0, "lack"),
    (100.0, "low"),
    (150.0, "medium"),
]

# 各绿地类型复合肥常规单次用量（kg/㎡）与年施肥次数
GREEN_TYPE_PLAN = {
    "park":        {"dosage": 0.05, "frequency": "每年 2-3 次"},
    "street":      {"dosage": 0.04, "frequency": "每年 2 次"},
    "road":        {"dosage": 0.04, "frequency": "每年 1-2 次"},
    "residential": {"dosage": 0.05, "frequency": "每年 2 次"},
    "attached":    {"dosage": 0.04, "frequency": "每年 2 次"},
    "other":       {"dosage": 0.04, "frequency": "每年 1-2 次"},
}


def grade(value, bands, highest):
    if value is None:
        return None
    for threshold, level in bands:
        if value < threshold:
            return level
    return highest


def grade_ph(value):
    return grade(value, PH_BANDS, "strong_alkaline")


def grade_organic(value):
    return grade(value, ORGANIC_BANDS, "high")


def grade_nitrogen(value):
    return grade(value, NITROGEN_BANDS, "high")


def grade_phosphorus(value):
    return grade(value, PHOSPHORUS_BANDS, "high")


def grade_potassium(value):
    return grade(value, POTASSIUM_BANDS, "high")


def grade_all(values):
    """values 含 ph/organic/nitrogen/phosphorus/potassium，返回各项等级。"""

    return {
        "ph_level": grade_ph(values.get("ph_value")),
        "organic_level": grade_organic(values.get("organic_matter")),
        "nitrogen_level": grade_nitrogen(values.get("alkali_nitrogen")),
        "phosphorus_level": grade_phosphorus(values.get("available_phosphorus")),
        "potassium_level": grade_potassium(values.get("available_potassium")),
    }


def build_fertilizer_plan(green_type, levels, *, target_plants=None):
    """结合绿地类型与检测缺素情况给出配方建议。

    返回的字段对应 SoilTest 上的配方列；缺素时优先建议单质肥矫正，
    常规情况推荐平衡型复合肥，有机质不足时叠加有机肥改土。
    """

    base = GREEN_TYPE_PLAN.get(green_type, GREEN_TYPE_PLAN["other"])
    n_level = levels.get("nitrogen_level")
    p_level = levels.get("phosphorus_level")
    k_level = levels.get("potassium_level")
    organic_level = levels.get("organic_level")
    ph_level = levels.get("ph_level")

    lacking = [
        ("氮", n_level in {"lack", "low"}),
        ("磷", p_level in {"lack", "low"}),
        ("钾", k_level in {"lack", "low"}),
    ]
    lacking_names = [name for name, lacking in lacking if lacking]

    advice = []
    if n_level == "lack":
        fertilizer_type = "urea"
        fertilizer_name = "尿素"
        nutrient_ratio = "N 46%"
        method = "furrow"
    elif p_level == "lack":
        fertilizer_type = "phosphate"
        fertilizer_name = "过磷酸钙"
        nutrient_ratio = "P₂O₅ 16%"
        method = "hole"
    elif k_level == "lack":
        fertilizer_type = "potassium"
        fertilizer_name = "硫酸钾"
        nutrient_ratio = "K₂O 50%"
        method = "hole"
    elif lacking_names:
        fertilizer_type = "compound"
        fertilizer_name = "三元复合肥"
        nutrient_ratio = "15-15-15"
        method = "broadcast"
    else:
        fertilizer_type = "slow_release"
        fertilizer_name = "缓释复合肥"
        nutrient_ratio = "18-9-18"
        method = "broadcast"

    if organic_level in {"very_low", "low"}:
        advice.append(
            f"有机质{('偏低' if organic_level == 'low' else '极低')}，建议每 ㎡ 增施腐熟有机肥 1.5-2.5kg 改土培肥"
        )
    if lacking_names:
        advice.append(f"检测显示{'、'.join(lacking_names)}素不足，配方中相应提高养分配比并配合追肥")
    if ph_level == "strong_acid":
        advice.append("土壤强酸性，建议施用生石灰或土壤调理剂 75-100g/㎡ 调酸后再施肥")
    elif ph_level == "acid":
        advice.append("土壤偏酸，可适量施用白云石粉或草木灰调节酸碱度")
    elif ph_level in {"alkaline", "strong_alkaline"}:
        advice.append("土壤偏碱，建议施用腐殖酸、石膏或硫磺粉改良，化肥选用生理酸性品种")
    if target_plants:
        advice.append(f"施肥方式与用量需兼顾目标植物（{target_plants}）的需肥特性")
    advice.append("施肥后及时浇透水，避开高温时段与雨天前作业")

    return {
        "fertilizer_type": fertilizer_type,
        "fertilizer_name": fertilizer_name,
        "nutrient_ratio": nutrient_ratio,
        "dosage_per_sqm": base["dosage"],
        "application_frequency": base["frequency"],
        "application_method": method,
        "application_period": "春季返青前及秋季生长末期",
        "formula_advice": "；".join(advice),
    }

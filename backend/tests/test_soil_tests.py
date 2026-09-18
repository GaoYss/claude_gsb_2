"""土壤检测档案与施肥作业接口测试。"""

from datetime import date

import pytest


def soil_payload(space_id, **overrides):
    payload = {
        "green_space_id": space_id,
        "sample_date": "2026-04-10",
        "sample_point": "中心草坪东南角",
        "sample_depth": 20,
        "lab": "杭州市园林绿化质量检测中心",
        "lab_report_no": "TR20260410-01",
        "texture": "loam",
        "ph": 6.4,
        "organic_matter": 18.5,
        "alkaline_n": 82,
        "available_p": 8.2,
        "available_k": 92,
        "target_crop": "马尼拉草坪",
        "formula_items": [
            {
                "product_name": "腐熟有机肥",
                "nutrient_ratio": "有机质≥45%",
                "dose": 150,
                "dose_unit": "kg_per_mu",
                "method": "broadcast",
                "timing": "秋季基肥",
            },
            {
                "product_name": "氮磷钾复合肥",
                "nutrient_ratio": "15-15-15",
                "dose": 30,
                "dose_unit": "kg_per_mu",
                "method": "furrow",
                "timing": "春季返青前",
            },
        ],
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------- 检测登记
def test_create_soil_test_generates_code_and_grades(api, make_space):
    space = make_space()
    data = api.data(api.post("/api/v1/soil-tests", soil_payload(space.id)), 201)
    assert data["test_no"].startswith("ST-")
    assert data["sample_point"] == "中心草坪东南角"
    assert data["texture_label"] == "壤土"
    assert data["ph"] == 6.4
    # pH 6.4 落在 5.5~6.5 之间属偏酸（low）；有效磷 8.2 偏低
    assert data["grades"]["ph"] == "low"
    assert data["grades"]["available_p"] == "low"
    assert data["grades"]["available_k"] == "low"
    assert len(data["formula_items"]) == 2
    assert data["formula_items"][0]["dose_unit_label"] == "千克/亩"


def test_advice_auto_generated_when_missing(api, make_space):
    space = make_space()
    payload = soil_payload(space.id, fert_advice=None, ph=6.8, organic_matter=24,
                           alkaline_n=105, available_p=16, available_k=130)
    data = api.data(api.post("/api/v1/soil-tests", payload), 201)
    assert data["fert_advice"]
    assert "马尼拉草坪" in data["fert_advice"]


def test_manual_advice_is_kept(api, make_space):
    space = make_space()
    data = api.data(
        api.post("/api/v1/soil-tests", soil_payload(space.id, fert_advice="结合秋施基肥重点补磷")),
        201,
    )
    assert data["fert_advice"] == "结合秋施基肥重点补磷"


def test_soil_test_validates_indicator_range_and_required(api, make_space):
    space = make_space()
    response = api.post("/api/v1/soil-tests", soil_payload(
        space.id, sample_point="", lab="", ph=12, organic_matter=-3))
    assert response.status_code == 422
    details = response.get_json()["data"]
    assert set(details) >= {"sample_point", "lab", "ph", "organic_matter"}


def test_sample_date_cannot_precede_established_date(api, make_space):
    space = make_space(established_date=date(2020, 1, 1))
    response = api.post("/api/v1/soil-tests", soil_payload(space.id, sample_date="2019-05-01"))
    assert response.status_code == 422
    assert "建成日期" in response.get_json()["data"]["sample_date"]


def test_nested_formula_item_errors_are_indexed(api, make_space):
    space = make_space()
    payload = soil_payload(space.id, formula_items=[
        {"product_name": "", "dose": -5, "dose_unit": "bad"},
        {"product_name": "复合肥", "dose": 30, "dose_unit": "kg_per_mu", "method": "sprinkle"},
    ])
    response = api.post("/api/v1/soil-tests", payload)
    assert response.status_code == 422
    details = response.get_json()["data"]
    assert "formula_items.0.product_name" in details
    assert "formula_items.0.dose" in details
    assert "formula_items.0.dose_unit" in details
    assert "formula_items.1.method" in details


# --------------------------------------------------------------- 更新与配方同步
def test_update_syncs_formula_items(api, make_space):
    space = make_space()
    created = api.data(api.post("/api/v1/soil-tests", soil_payload(space.id)), 201)
    first_item_id = created["formula_items"][0]["id"]
    second_item_id = created["formula_items"][1]["id"]

    updated = api.data(api.put(f"/api/v1/soil-tests/{created['id']}", soil_payload(
        space.id,
        ph=7.0,
        formula_items=[
            {"id": first_item_id, "product_name": "腐熟羊粪", "dose": 180,
             "dose_unit": "kg_per_mu", "method": "broadcast", "timing": "秋施"},
            {"product_name": "硫酸钾", "dose": 10, "dose_unit": "kg_per_mu",
             "method": "hole", "timing": "夏季"},
        ],
    )))
    assert updated["ph"] == 7.0
    names = [item["product_name"] for item in updated["formula_items"]]
    assert names == ["腐熟羊粪", "硫酸钾"]
    # 未保留 id 的旧明细被删除
    remaining_ids = [item["id"] for item in updated["formula_items"]]
    assert first_item_id in remaining_ids
    assert second_item_id not in remaining_ids


# --------------------------------------------------------------- 列表 / 汇总 / 对比
@pytest.fixture()
def make_soil_test(make_space):
    from app.services import SoilTestService

    counter = {"n": 0}

    def _make(space=None, **overrides):
        counter["n"] += 1
        space = space or make_space()
        payload = {
            "green_space_id": space.id,
            "sample_date": date(2026, min(counter["n"], 8), 15),
            "sample_point": f"采样点{counter['n']}",
            "lab": "杭州市园林绿化质量检测中心",
            "ph": round(6.5 + counter["n"] * 0.2, 2),
            "formula_items": [{
                "product_name": "复合肥", "dose": 30, "dose_unit": "kg_per_mu",
                "method": "furrow", "timing": "春季",
            }],
        }
        payload.update(overrides)
        return SoilTestService.create(payload)

    return _make


def test_list_filters_by_green_space_and_lab(api, make_soil_test, make_space):
    target = make_space(name="目标绿地")
    make_soil_test(space=target)
    make_soil_test()

    data = api.data(api.get("/api/v1/soil-tests", green_space_id=target.id))
    assert data["meta"]["total"] == 1
    assert data["items"][0]["green_space_id"] == target.id
    assert data["summary"]["total_count"] == 1
    assert data["summary"]["avg"]["ph"] is not None


def test_comparison_returns_deltas_for_same_green_space(api, make_soil_test, make_space):
    space = make_space(name="对比绿地")
    first = make_soil_test(space=space)
    second = make_soil_test(space=space)

    data = api.data(api.get("/api/v1/soil-tests/comparison", green_space_id=space.id))
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == first.id
    assert data["items"][1]["id"] == second.id
    # 第二次 pH 比第一次高 0.2
    assert data["items"][1]["deltas"]["ph"] == 0.2
    assert data["items"][0]["deltas"]["ph"] is None
    indicators = {item["key"] for item in data["indicators"]}
    assert indicators == {"ph", "organic_matter", "alkaline_n", "available_p", "available_k"}


def test_comparison_empty_for_green_space_without_test(api, make_space):
    space = make_space()
    data = api.data(api.get("/api/v1/soil-tests/comparison", green_space_id=space.id))
    assert data["items"] == []
    assert data["latest_fert_advice"] is None


def test_formula_options_lists_latest_tests(api, make_soil_test, make_space):
    space = make_space(name="配方绿地")
    make_soil_test(space=space)
    make_soil_test(space=space)

    data = api.data(api.get("/api/v1/soil-tests/formula-options", green_space_id=space.id))
    assert len(data["items"]) == 2
    # 最新检测排在最前
    assert data["items"][0]["sample_date"] >= data["items"][1]["sample_date"]
    assert data["items"][0]["formula_items"][0]["product_name"] == "复合肥"


# --------------------------------------------------------------- 施肥作业
@pytest.fixture()
def make_fertilization(make_space):
    from app.services import FertilizationService

    def _make(space=None, soil_test=None, formula_item=None, **overrides):
        space = space or (soil_test.green_space if soil_test else make_space())
        if soil_test is None and formula_item is not None:
            soil_test = formula_item.soil_test
        payload = {
            "green_space_id": space.id,
            "product_name": "氮磷钾复合肥",
            "actual_dose": 28.5,
            "actual_unit": "kg_per_mu",
            "method": "furrow",
            "fert_date": date(2026, 4, 20),
            "operator": "赵春生",
        }
        if soil_test is not None:
            payload["soil_test_id"] = soil_test.id
        if formula_item is not None:
            payload["formula_item_id"] = formula_item.id
            payload["planned_dose"] = float(formula_item.dose or 0)
            payload["planned_unit"] = formula_item.dose_unit
        payload.update(overrides)
        return FertilizationService.create(payload)

    return _make


def test_create_fertilization_referencing_formula(api, make_space):
    space = make_space()
    created = api.data(api.post("/api/v1/soil-tests", soil_payload(space.id)), 201)
    item = created["formula_items"][1]

    data = api.data(api.post("/api/v1/fertilizations", {
        "green_space_id": space.id,
        "soil_test_id": created["id"],
        "formula_item_id": item["id"],
        "product_name": item["product_name"],
        "planned_dose": item["dose"],
        "planned_unit": item["dose_unit"],
        "actual_dose": 32,
        "actual_unit": "kg_per_mu",
        "method": "furrow",
        "fert_date": "2026-04-20",
        "operator": "赵春生",
    }), 201)
    assert data["fert_no"].startswith("FT-")
    assert data["formula_item"]["product_name"] == "氮磷钾复合肥"
    assert data["planned_dose"] == 30.0
    assert data["actual_dose"] == 32.0
    assert data["actual_unit_label"] == "千克/亩"
    assert data["soil_test"]["test_no"] == created["test_no"]


def test_formula_must_belong_to_same_green_space(api, make_soil_test, make_space):
    other_space = make_space(name="无关绿地")
    soil_test = make_soil_test()
    item_id = soil_test.formula_items[0].id

    response = api.post("/api/v1/fertilizations", {
        "green_space_id": other_space.id,
        "formula_item_id": item_id,
        "product_name": "复合肥",
        "actual_dose": 30,
        "actual_unit": "kg_per_mu",
        "fert_date": "2026-04-20",
    })
    assert response.status_code == 422
    assert "不属于该绿地" in response.get_json()["data"]["formula_item_id"]


def test_referencing_formula_snapshots_planned_dose(api, make_space):
    """只选配方时，建议用量与肥料名称由后端自动带出。"""

    space = make_space()
    created = api.data(api.post("/api/v1/soil-tests", soil_payload(space.id)), 201)
    item = created["formula_items"][0]

    data = api.data(api.post("/api/v1/fertilizations", {
        "green_space_id": space.id,
        "formula_item_id": item["id"],
        "actual_dose": 140,
        "fert_date": "2026-10-15",
    }), 201)
    assert data["product_name"] == "腐熟有机肥"
    assert data["planned_dose"] == 150.0
    assert data["planned_unit"] == "kg_per_mu"
    assert data["soil_test_id"] == created["id"]


def test_standalone_fertilization_without_formula(api, make_space):
    space = make_space()
    data = api.data(api.post("/api/v1/fertilizations", {
        "green_space_id": space.id,
        "product_name": "自制堆肥",
        "actual_dose": 200,
        "actual_unit": "kg_per_mu",
        "method": "broadcast",
        "fert_date": "2026-05-01",
    }), 201)
    assert data["soil_test_id"] is None
    assert data["formula_item_id"] is None
    assert data["planned_dose"] is None


def test_fertilization_requires_actual_dose(api, make_space):
    space = make_space()
    response = api.post("/api/v1/fertilizations", {
        "green_space_id": space.id,
        "product_name": "复合肥",
        "fert_date": "2026-05-01",
    })
    assert response.status_code == 422
    assert "actual_dose" in response.get_json()["data"]


def test_fertilization_summary_and_filter(api, make_fertilization, make_soil_test):
    soil_test = make_soil_test()
    item = soil_test.formula_items[0]
    make_fertilization(soil_test=soil_test, formula_item=item, actual_dose=32)
    make_fertilization(soil_test=soil_test, formula_item=item, actual_dose=28)
    make_fertilization(actual_dose=50, method="broadcast")

    data = api.data(api.get("/api/v1/fertilizations/summary", soil_test_id=soil_test.id))
    assert data["total_count"] == 2
    assert data["total_actual_dose"] == 60.0
    assert data["referenced_count"] == 2
    assert data["reference_rate"] == 100.0

    listing = api.data(api.get("/api/v1/fertilizations", method="broadcast"))
    assert listing["meta"]["total"] == 1


def test_fertilization_links_maintenance_record_of_same_space(api, make_record, make_space):
    record = make_record()
    other_space = make_space(name="另一块绿地")
    response = api.post("/api/v1/fertilizations", {
        "green_space_id": other_space.id,
        "maintenance_record_id": record.id,
        "product_name": "复合肥",
        "actual_dose": 20,
        "fert_date": "2026-04-20",
    })
    assert response.status_code == 422
    assert "不属于所选绿地" in response.get_json()["data"]["maintenance_record_id"]


# --------------------------------------------------------------- 配方回填联动与删除
def test_soil_test_detail_aggregates_applications(api, make_space):
    space = make_space()
    created = api.data(api.post("/api/v1/soil-tests", soil_payload(space.id)), 201)
    item = created["formula_items"][0]
    for dose in (140, 150):
        api.data(api.post("/api/v1/fertilizations", {
            "green_space_id": space.id,
            "formula_item_id": item["id"],
            "actual_dose": dose,
            "fert_date": "2026-10-20",
        }), 201)

    detail = api.data(api.get(f"/api/v1/soil-tests/{created['id']}"))
    first = detail["formula_items"][0]
    assert first["application_count"] == 2
    assert first["actual_dose_total"] == 290.0
    assert len(first["applications"]) == 2


def test_deleting_soil_test_keeps_fertilization_history(api, make_space):
    space = make_space()
    created = api.data(api.post("/api/v1/soil-tests", soil_payload(space.id)), 201)
    item = created["formula_items"][0]
    fert = api.data(api.post("/api/v1/fertilizations", {
        "green_space_id": space.id,
        "formula_item_id": item["id"],
        "actual_dose": 140,
        "fert_date": "2026-10-20",
    }), 201)

    api.delete(f"/api/v1/soil-tests/{created['id']}")
    remaining = api.data(api.get(f"/api/v1/fertilizations/{fert['id']}"))
    assert remaining["soil_test_id"] is None
    assert remaining["formula_item_id"] is None
    assert remaining["product_name"] == "腐熟有机肥"
    assert remaining["actual_dose"] == 140.0


def test_green_space_delete_protection_counts_soil_data(api, make_space):
    space = make_space()
    api.post("/api/v1/soil-tests", soil_payload(space.id))

    response = api.delete(f"/api/v1/green-spaces/{space.id}")
    assert response.status_code == 409
    details = response.get_json()["data"]
    assert details["soil_test"] == 1

    data = api.data(api.delete(f"/api/v1/green-spaces/{space.id}", force="true"))
    assert data["soil_test"] == 1
    remaining = api.data(api.get("/api/v1/soil-tests", green_space_id=space.id))
    assert remaining["meta"]["total"] == 0


def test_green_space_profile_includes_latest_soil_test(api, make_space):
    space = make_space()
    created = api.data(api.post("/api/v1/soil-tests", soil_payload(space.id)), 201)
    profile = api.data(api.get(f"/api/v1/green-spaces/{space.id}/profile"))
    assert profile["latest_soil_test"]["test_no"] == created["test_no"]
    assert profile["recent_soil_tests"][0]["id"] == created["id"]

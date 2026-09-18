"""土壤检测档案与施肥作业接口。"""

from flask import Blueprint, request

from ..schemas import (
    fertilization_filters,
    soil_test_filters,
    validate_fertilization,
    validate_soil_test,
)
from ..services import FertilizationService, SoilTestService
from ..utils.pagination import paginate, parse_page_args
from ..utils.requests import json_body
from ..utils.responses import created, ok

bp = Blueprint("soil_tests", __name__)


# ---------------------------------------------------------------- 土壤检测档案
@bp.get("/soil-tests")
def list_soil_tests():
    filters = soil_test_filters(request.args)
    page, page_size = parse_page_args()
    query = SoilTestService.list_tests(filters, request.args)
    data = paginate(query, page, page_size)
    data["summary"] = SoilTestService.summary(filters)
    return ok(data)


@bp.get("/soil-tests/summary")
def soil_test_summary():
    return ok(SoilTestService.summary(soil_test_filters(request.args)))


@bp.get("/soil-tests/comparison")
def soil_test_comparison():
    """同一绿地多次检测结果对比。"""

    green_space_id = request.args.get("green_space_id", type=int)
    if not green_space_id:
        return ok({"green_space": None, "indicators": [], "items": [], "latest_fert_advice": None})
    return ok(SoilTestService.comparison(green_space_id))


@bp.get("/soil-tests/formula-options")
def soil_formula_options():
    """施肥登记时引用的候选配方（某绿地最近检测档案）。"""

    green_space_id = request.args.get("green_space_id", type=int)
    return ok({"items": SoilTestService.formula_options(green_space_id)})


@bp.post("/soil-tests")
def create_soil_test():
    payload = validate_soil_test(json_body())
    soil_test = SoilTestService.create(payload)
    return created(soil_test.to_dict(detail=True), message="土壤检测档案登记成功")


@bp.get("/soil-tests/<int:soil_test_id>")
def get_soil_test(soil_test_id):
    return ok(SoilTestService.detail(soil_test_id))


@bp.put("/soil-tests/<int:soil_test_id>")
def update_soil_test(soil_test_id):
    payload = validate_soil_test(json_body())
    soil_test = SoilTestService.update(soil_test_id, payload)
    return ok(soil_test.to_dict(detail=True), message="土壤检测档案已更新")


@bp.delete("/soil-tests/<int:soil_test_id>")
def delete_soil_test(soil_test_id):
    SoilTestService.delete(soil_test_id)
    return ok(None, message="土壤检测档案已删除")


# ---------------------------------------------------------------- 施肥作业
@bp.get("/fertilizations")
def list_fertilizations():
    filters = fertilization_filters(request.args)
    page, page_size = parse_page_args()
    query = FertilizationService.list_records(filters, request.args)
    data = paginate(query, page, page_size)
    data["summary"] = FertilizationService.summary(filters)
    return ok(data)


@bp.get("/fertilizations/summary")
def fertilization_summary():
    return ok(FertilizationService.summary(fertilization_filters(request.args)))


@bp.post("/fertilizations")
def create_fertilization():
    payload = validate_fertilization(json_body())
    record = FertilizationService.create(payload)
    return created(record.to_dict(detail=True), message="施肥作业登记成功")


@bp.get("/fertilizations/<int:fert_id>")
def get_fertilization(fert_id):
    return ok(FertilizationService.detail(fert_id))


@bp.put("/fertilizations/<int:fert_id>")
def update_fertilization(fert_id):
    payload = validate_fertilization(json_body())
    record = FertilizationService.update(fert_id, payload)
    return ok(record.to_dict(detail=True), message="施肥作业已更新")


@bp.delete("/fertilizations/<int:fert_id>")
def delete_fertilization(fert_id):
    FertilizationService.delete(fert_id)
    return ok(None, message="施肥作业已删除")

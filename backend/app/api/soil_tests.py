"""土壤检测档案与施肥作业接口。"""

from flask import Blueprint, request

from ..errors import ValidationError
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
    """同一绿地历次检测结果对比。"""

    green_space_id = request.args.get("green_space_id", type=int)
    if not green_space_id:
        raise ValidationError("对比失败", details={"green_space_id": "请选择需要对比的绿地"})
    return ok(SoilTestService.comparison(green_space_id))


@bp.post("/soil-tests")
def create_soil_test():
    payload = validate_soil_test(json_body())
    soil_test = SoilTestService.create(payload)
    return created(soil_test.to_dict(detail=True), message="土壤检测档案登记成功")


@bp.get("/soil-tests/<int:test_id>")
def get_soil_test(test_id):
    return ok(SoilTestService.detail(test_id))


@bp.put("/soil-tests/<int:test_id>")
def update_soil_test(test_id):
    payload = validate_soil_test(json_body())
    soil_test = SoilTestService.update(test_id, payload)
    return ok(soil_test.to_dict(detail=True), message="土壤检测档案已更新")


@bp.delete("/soil-tests/<int:test_id>")
def delete_soil_test(test_id):
    SoilTestService.delete(test_id)
    return ok(None, message="土壤检测档案已删除")


@bp.post("/soil-tests/<int:test_id>/regenerate-plan")
def regenerate_plan(test_id):
    """按当前检测结果重新生成施肥配方建议。"""

    soil_test = SoilTestService.regenerate_plan(test_id)
    return ok(soil_test.to_dict(detail=True), message="施肥配方已按检测结果重新生成")


# ---------------------------------------------------------------- 施肥作业
@bp.get("/fertilizations")
def list_fertilizations():
    filters = fertilization_filters(request.args)
    page, page_size = parse_page_args()
    query = FertilizationService.list_applications(filters, request.args)
    data = paginate(query, page, page_size)
    data["summary"] = FertilizationService.summary(filters)
    return ok(data)


@bp.get("/fertilizations/summary")
def fertilization_summary():
    return ok(FertilizationService.summary(fertilization_filters(request.args)))


@bp.post("/fertilizations")
def create_fertilization():
    payload = validate_fertilization(json_body())
    application = FertilizationService.create(payload)
    return created(application.to_dict(detail=True), message="施肥作业登记成功")


@bp.get("/fertilizations/<int:application_id>")
def get_fertilization(application_id):
    return ok(FertilizationService.detail(application_id))


@bp.put("/fertilizations/<int:application_id>")
def update_fertilization(application_id):
    payload = validate_fertilization(json_body())
    application = FertilizationService.update(application_id, payload)
    return ok(application.to_dict(detail=True), message="施肥作业已更新")


@bp.delete("/fertilizations/<int:application_id>")
def delete_fertilization(application_id):
    FertilizationService.delete(application_id)
    return ok(None, message="施肥作业已删除")

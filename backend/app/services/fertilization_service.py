"""施肥作业业务逻辑。"""

from sqlalchemy import func, or_

from ..errors import ValidationError
from ..extensions import db
from ..models import FertilizationRecord, GreenSpace, MaintenanceRecord, SoilFormulaItem, SoilTest
from ..utils.numbers import to_float
from ..utils.sorting import parse_sort
from .base_service import BaseService
from .code_generator import daily_prefix


class FertilizationService(BaseService):
    """施肥作业：引用检测档案中的施肥配方，回填实际用量与执行情况。"""

    model = FertilizationRecord
    label = "施肥作业"
    code_field = "fert_no"
    code_width = 3

    SORTABLE = {
        "fert_date": FertilizationRecord.fert_date,
        "actual_dose": FertilizationRecord.actual_dose,
        "fert_no": FertilizationRecord.fert_no,
        "created_at": FertilizationRecord.created_at,
    }

    @classmethod
    def code_prefix(cls):
        return daily_prefix("FT")

    # ------------------------------------------------------------ 校验与快照
    @classmethod
    def prepare_instance(cls, instance, payload):
        green_space_id = payload.get("green_space_id", instance.green_space_id)
        space = db.session.get(GreenSpace, green_space_id) if green_space_id else None
        if space is None:
            raise ValidationError("登记失败", details={"green_space_id": "所选绿地不存在"})

        item_id = payload.get("formula_item_id", instance.formula_item_id)
        test_id = payload.get("soil_test_id", instance.soil_test_id)
        item = db.session.get(SoilFormulaItem, item_id) if item_id else None
        if item_id:
            if item is None:
                raise ValidationError(
                    "登记失败", details={"formula_item_id": "所选施肥配方不存在"}
                )
            test = item.soil_test
            if test.green_space_id != space.id:
                raise ValidationError(
                    "登记失败",
                    details={"formula_item_id": "所选配方不属于该绿地的检测档案"},
                )
            test_id = test.id
        instance.soil_test_id = test_id

        if test_id and not item:
            test = db.session.get(SoilTest, test_id)
            if test is None:
                raise ValidationError(
                    "登记失败", details={"soil_test_id": "所选检测档案不存在"}
                )
            if test.green_space_id != space.id:
                raise ValidationError(
                    "登记失败", details={"soil_test_id": "所选检测档案不属于该绿地"}
                )

        record_id = payload.get("maintenance_record_id", instance.maintenance_record_id)
        if record_id:
            record = db.session.get(MaintenanceRecord, record_id)
            if record is None:
                raise ValidationError(
                    "登记失败", details={"maintenance_record_id": "关联的养护记录不存在"}
                )
            if record.green_space_id != space.id:
                raise ValidationError(
                    "登记失败",
                    details={"maintenance_record_id": "关联的养护记录不属于所选绿地"},
                )

        fert_date = payload.get("fert_date", instance.fert_date)
        if fert_date and space.established_date and fert_date < space.established_date:
            raise ValidationError(
                "登记失败",
                details={"fert_date": f"施肥日期不能早于该绿地建成日期 {space.established_date}"},
            )

        product_name = (payload.get("product_name") or instance.product_name)
        if not product_name and not item_id:
            raise ValidationError(
                "登记失败",
                details={"product_name": "请填写肥料名称，或选择施肥配方自动带出"},
            )

    @classmethod
    def apply_derived(cls, instance):
        """引用配方时，以配方为快照回填肥料名称与建议用量（允许人工再调整）。"""

        if instance.formula_item_id:
            item = db.session.get(SoilFormulaItem, instance.formula_item_id)
            if item is not None:
                if not instance.product_name:
                    instance.product_name = item.product_name
                if instance.planned_dose is None:
                    instance.planned_dose = item.dose
                if not instance.planned_unit:
                    instance.planned_unit = item.dose_unit
                if not instance.method:
                    instance.method = item.method

    # ------------------------------------------------------------ 查询
    @classmethod
    def _apply_filters(cls, query, filters):
        if filters.get("green_space_id"):
            query = query.filter(FertilizationRecord.green_space_id == filters["green_space_id"])
        if filters.get("soil_test_id"):
            query = query.filter(FertilizationRecord.soil_test_id == filters["soil_test_id"])
        if filters.get("formula_item_id"):
            query = query.filter(FertilizationRecord.formula_item_id == filters["formula_item_id"])
        if filters.get("maintenance_record_id"):
            query = query.filter(
                FertilizationRecord.maintenance_record_id == filters["maintenance_record_id"]
            )
        if filters.get("method"):
            query = query.filter(FertilizationRecord.method == filters["method"])
        if filters.get("date_from"):
            query = query.filter(FertilizationRecord.fert_date >= filters["date_from"])
        if filters.get("date_to"):
            query = query.filter(FertilizationRecord.fert_date <= filters["date_to"])
        keyword = filters.get("keyword")
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    FertilizationRecord.fert_no.like(like),
                    FertilizationRecord.product_name.like(like),
                    FertilizationRecord.operator.like(like),
                )
            )
        return query

    @classmethod
    def list_records(cls, filters, args):
        query = cls._apply_filters(db.session.query(FertilizationRecord), filters)
        return query.order_by(
            parse_sort(args, cls.SORTABLE, FertilizationRecord.fert_date.desc())
        )

    @classmethod
    def detail(cls, obj_id):
        return cls.get(obj_id).to_dict(detail=True)

    @classmethod
    def summary(cls, filters):
        """施肥汇总：作业次数、实际用量合计与配方执行率。"""

        query = cls._apply_filters(db.session.query(FertilizationRecord), filters)
        total, actual_sum, planned_sum, referenced = query.with_entities(
            func.count(FertilizationRecord.id),
            func.coalesce(func.sum(FertilizationRecord.actual_dose), 0),
            func.coalesce(func.sum(FertilizationRecord.planned_dose), 0),
            func.count(FertilizationRecord.formula_item_id),
        ).one()
        total = total or 0
        referenced = referenced or 0
        return {
            "total_count": total,
            "total_actual_dose": to_float(actual_sum) or 0,
            "total_planned_dose": to_float(planned_sum) or 0,
            "referenced_count": referenced,
            "reference_rate": round(referenced / total * 100, 1) if total else 0,
        }

    @classmethod
    def count_by_green_space(cls, space_id):
        return (
            db.session.query(func.count(FertilizationRecord.id))
            .filter(FertilizationRecord.green_space_id == space_id)
            .scalar()
            or 0
        )

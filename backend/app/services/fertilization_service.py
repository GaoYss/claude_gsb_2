"""施肥作业业务逻辑。

施肥作业必须引用一份土壤检测配方：登记时默认带出配方中的肥料与建议用量，
回填实际用量后计算与计划的偏差，用于评估配方执行情况。
"""

from decimal import Decimal

from sqlalchemy import func, or_

from ..errors import ValidationError
from ..extensions import db
from ..models import FertilizationApplication, SoilTest
from ..utils.dates import format_date
from ..utils.numbers import to_float
from ..utils.sorting import parse_sort
from .base_service import BaseService
from .code_generator import daily_prefix


class FertilizationService(BaseService):
    """施肥作业登记与实际用量回填。"""

    model = FertilizationApplication
    label = "施肥作业"
    code_field = "application_no"
    code_width = 3

    SORTABLE = {
        "plan_date": FertilizationApplication.plan_date,
        "applied_date": FertilizationApplication.applied_date,
        "actual_amount": FertilizationApplication.actual_amount,
        "created_at": FertilizationApplication.created_at,
    }

    @classmethod
    def code_prefix(cls):
        return daily_prefix("FA")

    # ------------------------------------------------------------ 校验与派生
    @classmethod
    def prepare_instance(cls, instance, payload):
        test_id = payload.get("soil_test_id", instance.soil_test_id)
        test = db.session.get(SoilTest, test_id) if test_id else None
        if test is None:
            raise ValidationError("登记失败", details={"soil_test_id": "引用的土壤检测档案不存在"})
        instance._test = test

        green_space_id = payload.get("green_space_id", instance.green_space_id)
        if green_space_id and green_space_id != test.green_space_id:
            raise ValidationError(
                "登记失败", details={"green_space_id": "施肥绿地与检测档案所属绿地不一致"}
            )

        plan_date = payload.get("plan_date", instance.plan_date)
        if plan_date and plan_date < test.sample_date:
            raise ValidationError(
                "登记失败",
                details={"plan_date": f"计划施肥日期不能早于采样日期 {format_date(test.sample_date)}"},
            )

        applied_date = payload.get("applied_date", instance.applied_date)
        if applied_date and plan_date and applied_date < test.sample_date:
            raise ValidationError(
                "登记失败",
                details={"applied_date": "实际施肥日期不能早于采样日期"},
            )

    @classmethod
    def apply_derived(cls, instance):
        test = getattr(instance, "_test", None) or db.session.get(SoilTest, instance.soil_test_id)
        # 绿地与配方保持一致
        instance.green_space_id = test.green_space_id

        # 新增时未指定的字段默认带出检测配方
        if instance.fertilizer_name is None and test.fertilizer_name:
            instance.fertilizer_name = test.fertilizer_name
        if instance.fertilizer_type is None and test.fertilizer_type:
            instance.fertilizer_type = test.fertilizer_type
        if instance.application_method is None and test.application_method:
            instance.application_method = test.application_method
        if instance.planned_dosage is None and test.dosage_per_sqm is not None:
            instance.planned_dosage = test.dosage_per_sqm

        # 计划/实际总用量优先按 单位用量 × 面积 推导
        cls._fill_total(instance, "planned_dosage", "planned_area", "planned_amount")
        cls._fill_total(instance, "actual_dosage", "actual_area", "actual_amount")

        # 回填实际用量后计算偏差
        if instance.actual_amount is not None and instance.planned_amount is not None:
            instance.deviation = (
                Decimal(str(instance.actual_amount)) - Decimal(str(instance.planned_amount))
            ).quantize(Decimal("0.01"))
        else:
            instance.deviation = None

        # 有实际用量/实际日期视为已施肥
        if instance.status == "applied" and instance.applied_date is None:
            instance.applied_date = instance.plan_date

    @staticmethod
    def _fill_total(instance, dosage_field, area_field, total_field):
        dosage = getattr(instance, dosage_field)
        area = getattr(instance, area_field)
        current = getattr(instance, total_field)
        if dosage is not None and area is not None:
            setattr(
                instance,
                total_field,
                (Decimal(str(dosage)) * Decimal(str(area))).quantize(Decimal("0.01")),
            )
        elif current is None and dosage is not None and area is None:
            setattr(instance, total_field, None)

    # ------------------------------------------------------------ 查询
    @classmethod
    def _apply_filters(cls, query, filters):
        if filters.get("soil_test_id"):
            query = query.filter(FertilizationApplication.soil_test_id == filters["soil_test_id"])
        if filters.get("green_space_id"):
            query = query.filter(FertilizationApplication.green_space_id == filters["green_space_id"])
        if filters.get("status"):
            query = query.filter(FertilizationApplication.status == filters["status"])
        if filters.get("fertilizer_type"):
            query = query.filter(
                FertilizationApplication.fertilizer_type == filters["fertilizer_type"]
            )
        if filters.get("date_from"):
            query = query.filter(FertilizationApplication.plan_date >= filters["date_from"])
        if filters.get("date_to"):
            query = query.filter(FertilizationApplication.plan_date <= filters["date_to"])
        keyword = filters.get("keyword")
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    FertilizationApplication.application_no.like(like),
                    FertilizationApplication.fertilizer_name.like(like),
                    FertilizationApplication.executor.like(like),
                    FertilizationApplication.worker.like(like),
                )
            )
        return query

    @classmethod
    def list_applications(cls, filters, args):
        query = cls._apply_filters(db.session.query(FertilizationApplication), filters)
        return query.order_by(
            parse_sort(args, cls.SORTABLE, FertilizationApplication.plan_date.desc())
        )

    @classmethod
    def detail(cls, obj_id):
        return cls.get(obj_id).to_dict(detail=True)

    @classmethod
    def summary(cls, filters):
        """施肥作业汇总：计划/已施数量、实际用量与偏差。"""

        total, planned_amount, actual_amount = cls._apply_filters(
            db.session.query(
                func.count(FertilizationApplication.id),
                func.coalesce(func.sum(FertilizationApplication.planned_amount), 0),
                func.coalesce(func.sum(FertilizationApplication.actual_amount), 0),
            ),
            filters,
        ).one()

        status_rows = (
            cls._apply_filters(
                db.session.query(
                    FertilizationApplication.status, func.count(FertilizationApplication.id)
                ),
                filters,
            )
            .group_by(FertilizationApplication.status)
            .all()
        )
        by_status = {code: 0 for code in ("planned", "applied", "skipped")}
        for status, count in status_rows:
            by_status[status] = count

        planned_kg = to_float(planned_amount) or 0
        actual_kg = to_float(actual_amount) or 0
        return {
            "total_count": total or 0,
            "planned_count": by_status["planned"],
            "applied_count": by_status["applied"],
            "skipped_count": by_status["skipped"],
            "planned_amount": planned_kg,
            "actual_amount": actual_kg,
            "deviation": round(actual_kg - planned_kg, 2),
            "by_status": by_status,
        }

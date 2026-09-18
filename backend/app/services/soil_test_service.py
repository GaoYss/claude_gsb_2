"""土壤检测档案业务逻辑。"""

from sqlalchemy import func, or_

from ..constants import NUTRIENT_LEVEL
from ..errors import ValidationError
from ..extensions import db
from ..models import FertilizationApplication, GreenSpace, SoilTest
from ..utils.dates import format_date
from ..utils.numbers import to_float
from ..utils.soil import build_fertilizer_plan, grade_all
from ..utils.sorting import parse_sort
from .base_service import BaseService
from .code_generator import daily_prefix

# 视为"缺素/偏低"的等级
LOW_NUTRIENT_LEVELS = {"lack", "low"}
LOW_ORGANIC_LEVELS = {"very_low", "low"}
ABNORMAL_PH_LEVELS = {"strong_acid", "acid", "alkaline", "strong_alkaline"}
NUTRIENT_FIELDS = ("nitrogen_level", "phosphorus_level", "potassium_level")


class SoilTestService(BaseService):
    """土壤检测档案：登记理化指标、自动分级并生成施肥配方。"""

    model = SoilTest
    label = "土壤检测档案"
    code_field = "test_no"
    code_width = 3

    SORTABLE = {
        "sample_date": SoilTest.sample_date,
        "test_no": SoilTest.test_no,
        "ph_value": SoilTest.ph_value,
        "organic_matter": SoilTest.organic_matter,
        "created_at": SoilTest.created_at,
    }

    @classmethod
    def code_prefix(cls):
        return daily_prefix("ST")

    # ------------------------------------------------------------ 校验与派生
    @classmethod
    def prepare_instance(cls, instance, payload):
        green_space_id = payload.get("green_space_id", instance.green_space_id)
        space = db.session.get(GreenSpace, green_space_id) if green_space_id else None
        if space is None:
            raise ValidationError("登记失败", details={"green_space_id": "所选绿地不存在"})

        sample_date = payload.get("sample_date", instance.sample_date)
        if sample_date and space.established_date and sample_date < space.established_date:
            raise ValidationError(
                "登记失败",
                details={"sample_date": f"采样日期不能早于该绿地建成日期 {space.established_date}"},
            )
        instance._space = space

    @classmethod
    def apply_derived(cls, instance):
        """指标分级落库；尚未填写配方时按绿地类型与缺素情况自动生成建议。"""

        levels = grade_all({
            "ph_value": instance.ph_value,
            "organic_matter": instance.organic_matter,
            "alkali_nitrogen": instance.alkali_nitrogen,
            "available_phosphorus": instance.available_phosphorus,
            "available_potassium": instance.available_potassium,
        })
        for field, value in levels.items():
            setattr(instance, field, value)

        if instance.fertilizer_type is None:
            space = getattr(instance, "_space", None) or db.session.get(
                GreenSpace, instance.green_space_id
            )
            plan = build_fertilizer_plan(
                space.green_type, levels, target_plants=instance.target_plants or None
            )
            for field, value in plan.items():
                setattr(instance, field, value)

    # ------------------------------------------------------------ 查询
    @classmethod
    def _apply_filters(cls, query, filters):
        if filters.get("green_space_id"):
            query = query.filter(SoilTest.green_space_id == filters["green_space_id"])
        if filters.get("soil_texture"):
            query = query.filter(SoilTest.soil_texture == filters["soil_texture"])
        if filters.get("date_from"):
            query = query.filter(SoilTest.sample_date >= filters["date_from"])
        if filters.get("date_to"):
            query = query.filter(SoilTest.sample_date <= filters["date_to"])
        for level_field in (
            "ph_level",
            "organic_level",
            "nitrogen_level",
            "phosphorus_level",
            "potassium_level",
        ):
            if filters.get(level_field):
                query = query.filter(getattr(SoilTest, level_field) == filters[level_field])
        keyword = filters.get("keyword")
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    SoilTest.test_no.like(like),
                    SoilTest.sample_point.like(like),
                    SoilTest.lab_org.like(like),
                    SoilTest.report_no.like(like),
                    SoilTest.target_plants.like(like),
                )
            )
        return query

    @classmethod
    def list_tests(cls, filters, args):
        query = cls._apply_filters(db.session.query(SoilTest), filters)
        return query.order_by(
            parse_sort(args, cls.SORTABLE, SoilTest.sample_date.desc())
        )

    @classmethod
    def detail(cls, obj_id):
        return cls.get(obj_id).to_dict(detail=True)

    @classmethod
    def regenerate_plan(cls, obj_id):
        """按当前检测结果重新生成配方建议（覆盖原配方）。"""

        instance = cls.get(obj_id)
        space = db.session.get(GreenSpace, instance.green_space_id)
        levels = {
            "ph_level": instance.ph_level,
            "organic_level": instance.organic_level,
            "nitrogen_level": instance.nitrogen_level,
            "phosphorus_level": instance.phosphorus_level,
            "potassium_level": instance.potassium_level,
        }
        plan = build_fertilizer_plan(
            space.green_type, levels, target_plants=instance.target_plants or None
        )
        for field, value in plan.items():
            setattr(instance, field, value)
        db.session.commit()
        return instance

    @classmethod
    def comparison(cls, green_space_id):
        """同一绿地历次检测的理化指标对比，按采样日期升序返回。"""

        space = db.session.get(GreenSpace, green_space_id)
        if space is None:
            raise ValidationError("对比失败", details={"green_space_id": "所选绿地不存在"})
        tests = (
            db.session.query(SoilTest)
            .filter(SoilTest.green_space_id == green_space_id)
            .order_by(SoilTest.sample_date.asc(), SoilTest.id.asc())
            .all()
        )
        return {
            "green_space": space.to_brief(),
            "items": [
                {
                    "id": item.id,
                    "test_no": item.test_no,
                    "sample_date": format_date(item.sample_date),
                    "sample_point": item.sample_point,
                    "lab_org": item.lab_org,
                    "ph_value": to_float(item.ph_value),
                    "ph_level": item.ph_level,
                    "organic_matter": to_float(item.organic_matter),
                    "organic_level": item.organic_level,
                    "alkali_nitrogen": to_float(item.alkali_nitrogen),
                    "nitrogen_level": item.nitrogen_level,
                    "available_phosphorus": to_float(item.available_phosphorus),
                    "phosphorus_level": item.phosphorus_level,
                    "available_potassium": to_float(item.available_potassium),
                    "potassium_level": item.potassium_level,
                    "application_count": len(item.applications),
                }
                for item in tests
            ],
        }

    @classmethod
    def latest_for_space(cls, green_space_id):
        return (
            db.session.query(SoilTest)
            .filter(SoilTest.green_space_id == green_space_id)
            .order_by(SoilTest.sample_date.desc(), SoilTest.id.desc())
            .first()
        )

    @classmethod
    def summary(cls, filters):
        """检测档案汇总：总量、覆盖绿地数与各类异常计数。"""

        base = cls._apply_filters(db.session.query(SoilTest), filters)
        total = base.with_entities(func.count(SoilTest.id)).scalar() or 0
        green_space_count = (
            cls._apply_filters(
                db.session.query(func.count(func.distinct(SoilTest.green_space_id))),
                filters,
            ).scalar()
            or 0
        )

        def _count(condition):
            return (
                cls._apply_filters(db.session.query(func.count(SoilTest.id)), filters)
                .filter(condition)
                .scalar()
                or 0
            )

        deficient = _count(
            or_(
                SoilTest.nitrogen_level.in_(LOW_NUTRIENT_LEVELS),
                SoilTest.phosphorus_level.in_(LOW_NUTRIENT_LEVELS),
                SoilTest.potassium_level.in_(LOW_NUTRIENT_LEVELS),
            )
        )
        low_organic = _count(SoilTest.organic_level.in_(LOW_ORGANIC_LEVELS))
        abnormal_ph = _count(SoilTest.ph_level.in_(ABNORMAL_PH_LEVELS))

        applied_test_ids = (
            db.session.query(FertilizationApplication.soil_test_id)
            .filter(FertilizationApplication.status == "applied")
            .distinct()
            .subquery()
        )
        applied_test_count = (
            cls._apply_filters(
                db.session.query(func.count(SoilTest.id)).join(
                    applied_test_ids, applied_test_ids.c.soil_test_id == SoilTest.id
                ),
                filters,
            ).scalar()
            or 0
        )

        return {
            "total_count": total,
            "green_space_count": green_space_count,
            "nutrient_deficient_count": deficient,
            "low_organic_count": low_organic,
            "abnormal_ph_count": abnormal_ph,
            "applied_test_count": applied_test_count,
            "nutrient_levels": NUTRIENT_LEVEL.options,
        }

"""土壤检测档案业务逻辑。"""

from sqlalchemy import func, or_

from ..constants import GREEN_SPACE_TYPE
from ..errors import ValidationError
from ..extensions import db
from ..models import FertilizationRecord, GreenSpace, SoilFormulaItem, SoilTest
from ..utils.numbers import to_float
from ..utils.soil import INDICATOR_DEFS, build_advice, indicator_meta
from ..utils.sorting import parse_sort
from .base_service import BaseService
from .code_generator import daily_prefix


class SoilTestService(BaseService):
    """土壤检测档案：检测登记、配方维护与同绿地多次检测对比。"""

    model = SoilTest
    label = "土壤检测档案"
    code_field = "test_no"
    code_width = 3
    nested_fields = ("formula_items",)

    SORTABLE = {
        "sample_date": SoilTest.sample_date,
        "test_no": SoilTest.test_no,
        "ph": SoilTest.ph,
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
        instance._green_type = space.green_type

        sample_date = payload.get("sample_date", instance.sample_date)
        if sample_date and space.established_date and sample_date < space.established_date:
            raise ValidationError(
                "登记失败",
                details={"sample_date": f"采样日期不能早于该绿地建成日期 {space.established_date}"},
            )

    @classmethod
    def apply_derived(cls, instance):
        """未填写施肥建议时，按各指标丰缺等级结合绿地类型与目标作物自动生成。"""

        if not instance.fert_advice:
            grades = instance.grades()
            green_type = GREEN_SPACE_TYPE.label(getattr(instance, "_green_type", None))
            instance.fert_advice = build_advice(
                grades, instance.target_crop, green_type
            )

    @classmethod
    def after_create(cls, instance, payload):
        if "formula_items" in payload:
            cls._sync_formula_items(instance, payload["formula_items"])

    @classmethod
    def after_update(cls, instance, payload):
        if "formula_items" in payload:
            cls._sync_formula_items(instance, payload["formula_items"])

    @classmethod
    def delete(cls, obj_id):
        """删除检测档案：配方明细随档案清除，施肥作业保留履历仅解除引用。"""

        instance = cls.get(obj_id)
        item_ids = [item.id for item in instance.formula_items]
        if item_ids:
            db.session.query(FertilizationRecord).filter(
                FertilizationRecord.formula_item_id.in_(item_ids)
            ).update({FertilizationRecord.formula_item_id: None}, synchronize_session=False)
        db.session.query(FertilizationRecord).filter(
            FertilizationRecord.soil_test_id == instance.id
        ).update({FertilizationRecord.soil_test_id: None}, synchronize_session=False)
        db.session.delete(instance)
        db.session.commit()
        return instance

    @staticmethod
    def _sync_formula_items(soil_test, items):
        """全量同步配方明细：按 id 更新已有项、新增新项、删除缺项。"""

        existing = {item.id: item for item in soil_test.formula_items}
        kept_ids = set()
        for raw in items:
            item_id = raw.get("id")
            if item_id and item_id in existing:
                item = existing[item_id]
                kept_ids.add(item_id)
            else:
                item = SoilFormulaItem(soil_test_id=soil_test.id)
                db.session.add(item)
            item.product_name = raw["product_name"]
            item.nutrient_ratio = raw.get("nutrient_ratio")
            item.dose = raw.get("dose")
            item.dose_unit = raw.get("dose_unit") or "kg_per_mu"
            item.method = raw.get("method")
            item.timing = raw.get("timing")
        for item_id, item in existing.items():
            if item_id not in kept_ids:
                db.session.query(FertilizationRecord).filter(
                    FertilizationRecord.formula_item_id == item_id
                ).update({FertilizationRecord.formula_item_id: None}, synchronize_session=False)
                db.session.delete(item)
        db.session.flush()

    # ------------------------------------------------------------ 查询
    @classmethod
    def _apply_filters(cls, query, filters):
        if filters.get("green_space_id"):
            query = query.filter(SoilTest.green_space_id == filters["green_space_id"])
        if filters.get("lab"):
            query = query.filter(SoilTest.lab.like(f"%{filters['lab']}%"))
        if filters.get("date_from"):
            query = query.filter(SoilTest.sample_date >= filters["date_from"])
        if filters.get("date_to"):
            query = query.filter(SoilTest.sample_date <= filters["date_to"])
        keyword = filters.get("keyword")
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    SoilTest.test_no.like(like),
                    SoilTest.sample_point.like(like),
                    SoilTest.lab.like(like),
                    SoilTest.lab_report_no.like(like),
                    SoilTest.target_crop.like(like),
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
    def formula_options(cls, green_space_id):
        """供施肥作业引用：某绿地最新检测档案及其配方明细。"""

        query = db.session.query(SoilTest)
        if green_space_id:
            query = query.filter(SoilTest.green_space_id == green_space_id)
        tests = query.order_by(SoilTest.sample_date.desc(), SoilTest.id.desc()).limit(10).all()
        return [
            {
                "id": test.id,
                "test_no": test.test_no,
                "sample_date": test.sample_date.isoformat(),
                "sample_point": test.sample_point,
                "target_crop": test.target_crop,
                "green_space": test.green_space.to_brief() if test.green_space else None,
                "formula_items": [item.to_dict() for item in test.formula_items],
            }
            for test in tests
        ]

    @classmethod
    def comparison(cls, green_space_id):
        """同一绿地多次检测结果对比，含各指标与上一次的差值。"""

        space = db.session.get(GreenSpace, green_space_id)
        if space is None:
            raise ValidationError("对比失败", details={"green_space_id": "所选绿地不存在"})

        tests = (
            db.session.query(SoilTest)
            .filter(SoilTest.green_space_id == green_space_id)
            .order_by(SoilTest.sample_date.asc(), SoilTest.id.asc())
            .all()
        )
        indicator_keys = list(INDICATOR_DEFS.keys())
        items = []
        previous = None
        for test in tests:
            values = test.indicator_values()
            grades = test.grades()
            deltas = {}
            for key in indicator_keys:
                current = to_float(values[key])
                if current is None or previous is None or previous[key] is None:
                    deltas[key] = None
                else:
                    deltas[key] = round(current - float(previous[key]), 2)
            items.append({
                "id": test.id,
                "test_no": test.test_no,
                "sample_date": test.sample_date.isoformat(),
                "sample_point": test.sample_point,
                "lab": test.lab,
                "target_crop": test.target_crop,
                "values": {key: to_float(values[key]) for key in indicator_keys},
                "grades": grades,
                "deltas": deltas,
            })
            previous = values

        return {
            "green_space": space.to_brief(),
            "indicators": list(indicator_meta().values()),
            "items": items,
            "latest_fert_advice": tests[-1].fert_advice if tests else None,
        }

    @classmethod
    def summary(cls, filters):
        """当前筛选条件下的检测次数与各指标平均值。"""

        query = cls._apply_filters(db.session.query(SoilTest), filters)
        totals = query.with_entities(
            func.count(SoilTest.id),
            func.avg(SoilTest.ph),
            func.avg(SoilTest.organic_matter),
            func.avg(SoilTest.alkaline_n),
            func.avg(SoilTest.available_p),
            func.avg(SoilTest.available_k),
        ).one()
        return {
            "total_count": totals[0] or 0,
            "avg": {
                "ph": to_float(totals[1]),
                "organic_matter": to_float(totals[2]),
                "alkaline_n": to_float(totals[3]),
                "available_p": to_float(totals[4]),
                "available_k": to_float(totals[5]),
            },
        }

    @classmethod
    def count_by_green_space(cls, space_id):
        return (
            db.session.query(func.count(SoilTest.id))
            .filter(SoilTest.green_space_id == space_id)
            .scalar()
            or 0
        )

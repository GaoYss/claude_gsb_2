"""土壤检测档案模型。

一条 :class:`SoilTest` 沉淀一次土壤检测的登记信息与检测结果，
检测后可结合目标作物与绿地类型给出 :class:`SoilFormulaItem` 施肥配方；
后续的 :class:`FertilizationRecord` 施肥作业引用配方项并回填实际用量。
"""

from ..constants import FERT_DOSE_UNIT, FERT_METHOD, SOIL_TEXTURE
from ..extensions import db
from ..utils.dates import format_date, format_datetime
from ..utils.numbers import to_float
from ..utils.soil import INDICATOR_DEFS, grade_of
from .mixins import TimestampMixin, quantity_column


def _indicator_value(value):
    return to_float(value, digits=2)


class SoilTest(TimestampMixin, db.Model):
    """土壤检测档案：采样登记、检测结果与施肥配方。"""

    __tablename__ = "soil_test"

    id = db.Column(db.Integer, primary_key=True)
    test_no = db.Column(db.String(32), nullable=False, unique=True, index=True)
    green_space_id = db.Column(
        db.Integer, db.ForeignKey("green_space.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sample_date = db.Column(db.Date, nullable=False, index=True)
    sample_point = db.Column(db.String(128), nullable=False)
    sample_depth = db.Column(quantity_column())
    lab = db.Column(db.String(128), nullable=False, index=True)
    lab_report_no = db.Column(db.String(64), index=True)
    texture = db.Column(db.String(16))

    # ---- 检测结果 -------------------------------------------------
    ph = db.Column(db.Numeric(4, 2))                       # 酸碱度（无量纲）
    organic_matter = db.Column(db.Numeric(8, 2))          # 有机质 g/kg
    alkaline_n = db.Column(db.Numeric(8, 2))              # 碱解氮 mg/kg
    available_p = db.Column(db.Numeric(8, 2))             # 有效磷 mg/kg
    available_k = db.Column(db.Numeric(8, 2))             # 速效钾 mg/kg

    # ---- 配方背景 -------------------------------------------------
    target_crop = db.Column(db.String(128))
    fert_advice = db.Column(db.Text)
    remark = db.Column(db.Text)

    green_space = db.relationship("GreenSpace", back_populates="soil_tests", lazy="joined")
    formula_items = db.relationship(
        "SoilFormulaItem",
        back_populates="soil_test",
        cascade="all, delete-orphan",
        order_by="SoilFormulaItem.id.asc()",
    )

    def indicator_values(self):
        """指标键 → 数值，供评级与历史对比复用。"""

        return {
            "ph": self.ph,
            "organic_matter": self.organic_matter,
            "alkaline_n": self.alkaline_n,
            "available_p": self.available_p,
            "available_k": self.available_k,
        }

    def grades(self):
        """各指标的丰缺等级（无值则不评级）。"""

        result = {}
        for key, value in self.indicator_values().items():
            if value is None:
                result[key] = None
            else:
                grade = grade_of(key, float(value))
                result[key] = grade
        return result

    def to_dict(self, detail=False):
        grades = self.grades()
        data = {
            "id": self.id,
            "test_no": self.test_no,
            "green_space_id": self.green_space_id,
            "green_space": self.green_space.to_brief() if self.green_space else None,
            "sample_date": format_date(self.sample_date),
            "sample_point": self.sample_point,
            "sample_depth": _indicator_value(self.sample_depth),
            "lab": self.lab,
            "lab_report_no": self.lab_report_no,
            "texture": self.texture,
            "texture_label": SOIL_TEXTURE.label(self.texture) if self.texture else None,
            "ph": _indicator_value(self.ph),
            "organic_matter": _indicator_value(self.organic_matter),
            "alkaline_n": _indicator_value(self.alkaline_n),
            "available_p": _indicator_value(self.available_p),
            "available_k": _indicator_value(self.available_k),
            "grades": grades,
            "target_crop": self.target_crop,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }
        if detail:
            data["fert_advice"] = self.fert_advice
            data["remark"] = self.remark
            data["formula_items"] = [item.to_dict(with_applications=True) for item in self.formula_items]
        return data


class SoilFormulaItem(db.Model):
    """施肥配方明细：检测档案下的一种肥料及其建议用量与施用法。"""

    __tablename__ = "soil_formula_item"

    id = db.Column(db.Integer, primary_key=True)
    soil_test_id = db.Column(
        db.Integer, db.ForeignKey("soil_test.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_name = db.Column(db.String(96), nullable=False)
    nutrient_ratio = db.Column(db.String(32))
    dose = db.Column(quantity_column())
    dose_unit = db.Column(db.String(16), nullable=False, default="kg_per_mu")
    method = db.Column(db.String(16))
    timing = db.Column(db.String(96))

    soil_test = db.relationship("SoilTest", back_populates="formula_items")
    fertilizations = db.relationship(
        "FertilizationRecord",
        back_populates="formula_item",
        order_by="FertilizationRecord.fert_date.desc(), FertilizationRecord.id.desc()",
    )

    def to_dict(self, with_applications=False):
        data = {
            "id": self.id,
            "soil_test_id": self.soil_test_id,
            "product_name": self.product_name,
            "nutrient_ratio": self.nutrient_ratio,
            "dose": to_float(self.dose),
            "dose_unit": self.dose_unit,
            "dose_unit_label": FERT_DOSE_UNIT.label(self.dose_unit),
            "method": self.method,
            "method_label": FERT_METHOD.label(self.method) if self.method else None,
            "timing": self.timing,
        }
        if with_applications:
            applications = [item.to_dict() for item in self.fertilizations]
            data["applications"] = applications
            data["application_count"] = len(applications)
            data["actual_dose_total"] = to_float(
                sum((item.actual_dose or 0) for item in self.fertilizations)
            ) or 0
        return data


class FertilizationRecord(TimestampMixin, db.Model):
    """施肥作业：引用某条施肥配方并回填实际用量。

    配方项随检测档案删除时，作业记录保留，配方关联置空并依赖名称/建议用量
    快照字段留存履历。
    """

    __tablename__ = "fertilization_record"

    id = db.Column(db.Integer, primary_key=True)
    fert_no = db.Column(db.String(32), nullable=False, unique=True, index=True)
    green_space_id = db.Column(
        db.Integer, db.ForeignKey("green_space.id", ondelete="CASCADE"), nullable=False, index=True
    )
    soil_test_id = db.Column(
        db.Integer, db.ForeignKey("soil_test.id", ondelete="SET NULL"), nullable=True, index=True
    )
    formula_item_id = db.Column(
        db.Integer, db.ForeignKey("soil_formula_item.id", ondelete="SET NULL"), nullable=True, index=True
    )
    maintenance_record_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_record.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    product_name = db.Column(db.String(96), nullable=False)
    planned_dose = db.Column(quantity_column())
    planned_unit = db.Column(db.String(16))
    actual_dose = db.Column(quantity_column(), nullable=False, default=0)
    actual_unit = db.Column(db.String(16), nullable=False, default="kg_per_mu")
    method = db.Column(db.String(16))
    fert_date = db.Column(db.Date, nullable=False, index=True)
    operator = db.Column(db.String(64))
    remark = db.Column(db.Text)

    green_space = db.relationship("GreenSpace", back_populates="fertilizations", lazy="joined")
    soil_test = db.relationship("SoilTest", lazy="joined")
    formula_item = db.relationship("SoilFormulaItem", back_populates="fertilizations", lazy="joined")
    record = db.relationship("MaintenanceRecord")

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "fert_no": self.fert_no,
            "green_space_id": self.green_space_id,
            "green_space": self.green_space.to_brief() if self.green_space else None,
            "soil_test_id": self.soil_test_id,
            "soil_test": (
                {
                    "id": self.soil_test.id,
                    "test_no": self.soil_test.test_no,
                    "sample_date": format_date(self.soil_test.sample_date),
                    "target_crop": self.soil_test.target_crop,
                }
                if self.soil_test
                else None
            ),
            "formula_item_id": self.formula_item_id,
            "formula_item": (
                {"id": self.formula_item.id, "product_name": self.formula_item.product_name}
                if self.formula_item
                else None
            ),
            "maintenance_record_id": self.maintenance_record_id,
            "record": (
                {
                    "id": self.record.id,
                    "record_no": self.record.record_no,
                    "record_date": format_date(self.record.record_date),
                }
                if self.record
                else None
            ),
            "product_name": self.product_name,
            "planned_dose": to_float(self.planned_dose),
            "planned_unit": self.planned_unit,
            "planned_unit_label": FERT_DOSE_UNIT.label(self.planned_unit) if self.planned_unit else None,
            "actual_dose": to_float(self.actual_dose),
            "actual_unit": self.actual_unit,
            "actual_unit_label": FERT_DOSE_UNIT.label(self.actual_unit),
            "method": self.method,
            "method_label": FERT_METHOD.label(self.method) if self.method else None,
            "fert_date": format_date(self.fert_date),
            "operator": self.operator,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }
        if detail:
            data["remark"] = self.remark
        return data

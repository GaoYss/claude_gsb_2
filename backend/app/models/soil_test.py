"""土壤检测档案与施肥作业模型。"""

from ..constants import (
    APPLICATION_STATUS,
    FERTILIZATION_METHOD,
    FERTILIZER_TYPE,
    NUTRIENT_LEVEL,
    ORGANIC_LEVEL,
    PH_LEVEL,
    SOIL_TEXTURE,
)
from ..extensions import db
from ..utils.dates import format_date, format_datetime
from ..utils.numbers import to_float
from .mixins import TimestampMixin, amount_column, quantity_column


class SoilTest(TimestampMixin, db.Model):
    """土壤检测档案：一次采样检测及其施肥配方。"""

    __tablename__ = "soil_test"

    id = db.Column(db.Integer, primary_key=True)
    test_no = db.Column(db.String(32), nullable=False, unique=True, index=True)
    green_space_id = db.Column(
        db.Integer, db.ForeignKey("green_space.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sample_date = db.Column(db.Date, nullable=False, index=True)
    sample_point = db.Column(db.String(128), nullable=False)
    sample_depth = db.Column(quantity_column())
    lab_org = db.Column(db.String(128), nullable=False)
    report_no = db.Column(db.String(64), index=True)
    soil_texture = db.Column(db.String(32), index=True)

    # 理化指标
    ph_value = db.Column(db.Numeric(4, 2))
    ph_level = db.Column(db.String(16))
    organic_matter = db.Column(db.Numeric(6, 2))          # 有机质 g/kg（部分地区按 %）
    organic_level = db.Column(db.String(16))
    alkali_nitrogen = db.Column(db.Numeric(8, 2))         # 碱解氮 mg/kg
    nitrogen_level = db.Column(db.String(16))
    available_phosphorus = db.Column(db.Numeric(8, 2))    # 有效磷 mg/kg
    phosphorus_level = db.Column(db.String(16))
    available_potassium = db.Column(db.Numeric(8, 2))     # 速效钾 mg/kg
    potassium_level = db.Column(db.String(16))
    bulk_density = db.Column(db.Numeric(5, 2))            # 容重 g/cm³
    salinity = db.Column(db.Numeric(6, 3))                # 全盐量 g/kg
    moisture = db.Column(db.Numeric(5, 2))                # 土壤含水率 %

    # 目标作物/绿地与施肥配方
    target_plants = db.Column(db.String(255))
    fertilizer_type = db.Column(db.String(32))
    fertilizer_name = db.Column(db.String(96))
    nutrient_ratio = db.Column(db.String(64))
    dosage_per_sqm = db.Column(db.Numeric(8, 3))          # 建议用量 kg/㎡
    application_frequency = db.Column(db.String(64))
    application_method = db.Column(db.String(32))
    application_period = db.Column(db.String(128))
    formula_advice = db.Column(db.Text)

    conclusion = db.Column(db.Text)
    operator = db.Column(db.String(64))
    remark = db.Column(db.Text)

    green_space = db.relationship("GreenSpace", back_populates="soil_tests", lazy="joined")
    applications = db.relationship(
        "FertilizationApplication",
        back_populates="soil_test",
        cascade="all, delete-orphan",
        order_by="FertilizationApplication.plan_date.desc(), FertilizationApplication.id.desc()",
    )

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "test_no": self.test_no,
            "green_space_id": self.green_space_id,
            "green_space": self.green_space.to_brief() if self.green_space else None,
            "sample_date": format_date(self.sample_date),
            "sample_point": self.sample_point,
            "sample_depth": to_float(self.sample_depth),
            "lab_org": self.lab_org,
            "report_no": self.report_no,
            "soil_texture": self.soil_texture,
            "soil_texture_label": SOIL_TEXTURE.label(self.soil_texture) if self.soil_texture else None,
            "ph_value": to_float(self.ph_value),
            "ph_level": self.ph_level,
            "ph_level_label": PH_LEVEL.label(self.ph_level) if self.ph_level else None,
            "organic_matter": to_float(self.organic_matter),
            "organic_level": self.organic_level,
            "organic_level_label": ORGANIC_LEVEL.label(self.organic_level) if self.organic_level else None,
            "alkali_nitrogen": to_float(self.alkali_nitrogen),
            "nitrogen_level": self.nitrogen_level,
            "nitrogen_level_label": NUTRIENT_LEVEL.label(self.nitrogen_level) if self.nitrogen_level else None,
            "available_phosphorus": to_float(self.available_phosphorus),
            "phosphorus_level": self.phosphorus_level,
            "phosphorus_level_label": (
                NUTRIENT_LEVEL.label(self.phosphorus_level) if self.phosphorus_level else None
            ),
            "available_potassium": to_float(self.available_potassium),
            "potassium_level": self.potassium_level,
            "potassium_level_label": (
                NUTRIENT_LEVEL.label(self.potassium_level) if self.potassium_level else None
            ),
            "bulk_density": to_float(self.bulk_density),
            "salinity": to_float(self.salinity),
            "moisture": to_float(self.moisture),
            "target_plants": self.target_plants,
            "fertilizer_type": self.fertilizer_type,
            "fertilizer_type_label": (
                FERTILIZER_TYPE.label(self.fertilizer_type) if self.fertilizer_type else None
            ),
            "fertilizer_name": self.fertilizer_name,
            "nutrient_ratio": self.nutrient_ratio,
            "dosage_per_sqm": to_float(self.dosage_per_sqm),
            "application_frequency": self.application_frequency,
            "application_method": self.application_method,
            "application_method_label": (
                FERTILIZATION_METHOD.label(self.application_method)
                if self.application_method
                else None
            ),
            "application_period": self.application_period,
            "application_count": len(self.applications),
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }
        if detail:
            data["formula_advice"] = self.formula_advice
            data["conclusion"] = self.conclusion
            data["operator"] = self.operator
            data["remark"] = self.remark
            data["applications"] = [item.to_dict() for item in self.applications]
            total_applied = sum(to_float(item.actual_amount) or 0 for item in self.applications
                                if item.status == "applied")
            data["total_applied_amount"] = round(total_applied, 2)
        return data


class FertilizationApplication(TimestampMixin, db.Model):
    """施肥作业：引用某份土壤检测配方，并回填实际用量。"""

    __tablename__ = "fertilization_application"

    id = db.Column(db.Integer, primary_key=True)
    application_no = db.Column(db.String(32), nullable=False, unique=True, index=True)
    soil_test_id = db.Column(
        db.Integer, db.ForeignKey("soil_test.id", ondelete="CASCADE"), nullable=False, index=True
    )
    green_space_id = db.Column(
        db.Integer, db.ForeignKey("green_space.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_date = db.Column(db.Date, nullable=False, index=True)
    fertilizer_name = db.Column(db.String(96))
    fertilizer_type = db.Column(db.String(32))
    planned_dosage = db.Column(quantity_column())        # 计划用量 kg/㎡
    planned_area = db.Column(quantity_column())          # 计划施肥面积 ㎡
    planned_amount = db.Column(amount_column())          # 计划总用量 kg
    application_method = db.Column(db.String(32))
    executor = db.Column(db.String(64))
    status = db.Column(db.String(16), nullable=False, default="planned", index=True)

    applied_date = db.Column(db.Date)
    actual_dosage = db.Column(quantity_column())         # 实际用量 kg/㎡
    actual_area = db.Column(quantity_column())
    actual_amount = db.Column(amount_column())           # 实际总用量 kg
    deviation = db.Column(db.Numeric(8, 2))              # 实际-计划（kg）
    worker = db.Column(db.String(64))
    work_hours = db.Column(quantity_column())
    remark = db.Column(db.Text)

    soil_test = db.relationship("SoilTest", back_populates="applications")
    green_space = db.relationship("GreenSpace", lazy="joined")

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "application_no": self.application_no,
            "soil_test_id": self.soil_test_id,
            "test_no": self.soil_test.test_no if self.soil_test else None,
            "green_space_id": self.green_space_id,
            "green_space": self.green_space.to_brief() if self.green_space else None,
            "plan_date": format_date(self.plan_date),
            "fertilizer_name": self.fertilizer_name,
            "fertilizer_type": self.fertilizer_type,
            "fertilizer_type_label": (
                FERTILIZER_TYPE.label(self.fertilizer_type) if self.fertilizer_type else None
            ),
            "planned_dosage": to_float(self.planned_dosage),
            "planned_area": to_float(self.planned_area),
            "planned_amount": to_float(self.planned_amount),
            "application_method": self.application_method,
            "application_method_label": (
                FERTILIZATION_METHOD.label(self.application_method)
                if self.application_method
                else None
            ),
            "executor": self.executor,
            "status": self.status,
            "status_label": APPLICATION_STATUS.label(self.status),
            "applied_date": format_date(self.applied_date),
            "actual_dosage": to_float(self.actual_dosage),
            "actual_area": to_float(self.actual_area),
            "actual_amount": to_float(self.actual_amount),
            "deviation": to_float(self.deviation),
            "worker": self.worker,
            "work_hours": to_float(self.work_hours),
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }
        if detail:
            data["remark"] = self.remark
        return data

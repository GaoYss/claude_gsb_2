"""测试夹具：内存 SQLite + 常用业务数据工厂。"""

import random
from datetime import date

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def payload_of(response, expected_status=200):
    """断言状态码并取出统一响应中的 data。"""

    assert response.status_code == expected_status, response.get_data(as_text=True)
    body = response.get_json()
    assert body["success"] is (expected_status < 400)
    return body["data"]


@pytest.fixture()
def api(client):
    class Api:
        def get(self, path, **params):
            return client.get(path, query_string=params)

        def post(self, path, json=None):
            return client.post(path, json=json or {})

        def put(self, path, json=None):
            return client.put(path, json=json or {})

        def patch(self, path, json=None):
            return client.patch(path, json=json or {})

        def delete(self, path, **params):
            return client.delete(path, query_string=params)

        data = staticmethod(payload_of)

    return Api()


@pytest.fixture()
def make_space(app):
    from app.services import GreenSpaceService

    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        payload = {
            "name": f"测试绿地{counter['n']}",
            "district": "西湖区",
            "green_type": "park",
            "maintenance_grade": "level2",
            "area_sqm": 1200,
            "established_date": date(2015, 5, 1),
        }
        payload.update(overrides)
        return GreenSpaceService.create(payload)

    return _make


@pytest.fixture()
def make_task(make_space):
    from app.services import MaintenanceTaskService

    def _make(space=None, **overrides):
        space = space or make_space()
        payload = {
            "green_space_id": space.id,
            "title": "春季修剪作业",
            "task_type": "prune",
            "plan_date": date(2026, 3, 10),
            "priority": "medium",
            "executor": "绿化一班",
        }
        payload.update(overrides)
        return MaintenanceTaskService.create(payload)

    return _make


@pytest.fixture()
def make_record(make_space):
    from app.services import MaintenanceRecordService

    def _make(space=None, task=None, **overrides):
        if task is not None:
            space = task.green_space
        space = space or make_space()
        payload = {
            "green_space_id": space.id,
            "record_date": date(2026, 3, 12),
            "work_content": "修剪香樟下垂枝 32 株",
            "worker": "王海涛",
            "work_hours": 6,
            "quality_result": "qualified",
        }
        if task is not None:
            payload["task_id"] = task.id
            payload.pop("green_space_id")
        payload.update(overrides)
        return MaintenanceRecordService.create(payload)

    return _make


@pytest.fixture()
def make_replacement(make_space):
    from app.services import PlantReplacementService

    def _make(space=None, record=None, **overrides):
        if record is not None:
            space = record.green_space
        space = space or make_space()
        payload = {
            "green_space_id": space.id,
            "plant_name": "香樟",
            "plant_category": "tree",
            "quantity": 10,
            "unit": "plant",
            "reason": "dead",
            "replace_date": date(2026, 3, 15),
            "unit_price": 128.5,
        }
        if record is not None:
            payload["maintenance_record_id"] = record.id
        payload.update(overrides)
        return PlantReplacementService.create(payload)

    return _make


@pytest.fixture()
def make_soil_test(make_space):
    from app.services import SoilTestService

    def _make(space=None, **overrides):
        space = space or make_space()
        payload = {
            "green_space_id": space.id,
            "sample_date": date(2026, 3, 1),
            "sample_point": "中央草坪 5 点混合样",
            "lab_org": "市园林科学研究所检测中心",
            "ph_value": 6.8,
            "organic_matter": 18.5,
            "alkali_nitrogen": 86.0,
            "available_phosphorus": 12.4,
            "available_potassium": 132.0,
            "target_plants": "马尼拉草坪、金森女贞",
        }
        payload.update(overrides)
        return SoilTestService.create(payload)

    return _make


@pytest.fixture()
def make_fertilization(make_soil_test):
    from app.services import FertilizationService

    def _make(test=None, **overrides):
        test = test or make_soil_test()
        payload = {
            "soil_test_id": test.id,
            "plan_date": date(2026, 3, 20),
            "planned_area": 2000,
            "executor": "绿化二班",
        }
        payload.update(overrides)
        return FertilizationService.create(payload)

    return _make


@pytest.fixture()
def seeded(app):
    """写入演示数据（固定随机种子，保证断言稳定）。"""

    from app.cli import generate_demo_data

    return generate_demo_data(random.Random(20260913))

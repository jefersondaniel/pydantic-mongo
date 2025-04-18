import pytest
from bson import ObjectId
from pydantic import BaseModel, ValidationError
from enum import Enum
from typing_extensions import Annotated
from typing import Optional

from pydantic_mongo import ObjectIdField, EnumAnnotation


class User(BaseModel):
    id: ObjectIdField


class State(Enum):
    PREPARATION = "Preparation"
    PROCESSING = "Processing"


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class Order(BaseModel):
    state: Annotated[State, EnumAnnotation[State]]
    color: Optional[Annotated[Color, EnumAnnotation[Color]]] = None


class TestFields:
    def test_object_id_field_validate(self):
        with pytest.raises(ValidationError):
            User.model_validate({"id": "lala"})
        User.model_validate({"id": "611827f2878b88b49ebb69fc"})
        User.model_validate({"id": ObjectId("611827f2878b88b49ebb69fc")})

    def test_object_id_field_json_schema(self):
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        schema = user.model_json_schema()
        assert {
            "title": "User",
            "type": "object",
            "properties": {"id": {"title": "Id", "type": "string"}},
            "required": ["id"],
        } == schema

    def test_object_id_field_dump_json(self):
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        json_dump = user.model_dump_json()
        assert '{"id":"611827f2878b88b49ebb69fc"}' == json_dump

    def test_object_id_field_dump(self):
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        python_dump = user.model_dump(mode="python")
        json_dump = user.model_dump(mode="json")
        assert {"id": ObjectId("611827f2878b88b49ebb69fc")} == python_dump
        assert {"id": "611827f2878b88b49ebb69fc"} == json_dump

    def test_object_id_field_conversion(self):
        user = User(id="611827f2878b88b49ebb69fc")
        assert user.id == ObjectId("611827f2878b88b49ebb69fc")

    def test_enum_field_dump(self):
        order = Order(state=State.PREPARATION, color=Color.RED)
        python_dump = order.model_dump(mode="python")
        json_dump = order.model_dump(mode="json")
        assert python_dump == {"state": "Preparation", "color": 1}
        assert json_dump == {"state": "Preparation", "color": 1}

    def test_enum_field_conversion(self):
        order = Order(state="Preparation", color=1)
        assert order.state == State.PREPARATION
        assert order.color == Color.RED
        order = Order(state=State.PREPARATION, color=Color.RED)
        assert order.state == State.PREPARATION
        assert order.color == Color.RED

    def test_enum_field_validation(self):
        with pytest.raises(ValidationError):
            Order(state="lala", color=1)
        Order(state=State.PREPARATION, color=Color.RED)  # Should not raise

    def test_enum_field_dump_json(self):
        order = Order(state=State.PREPARATION, color=Color.RED)
        json_dump = order.model_dump_json()
        assert json_dump == '{"state":"Preparation","color":1}'

    def test_enum_field_dump_json_with_none(self):
        order = Order(state=State.PREPARATION, color=None)
        json_dump = order.model_dump_json()
        assert json_dump == '{"state":"Preparation","color":null}'

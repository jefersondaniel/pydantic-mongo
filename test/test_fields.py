import pytest
from bson import ObjectId, BSON
from pydantic import BaseModel, ValidationError
from enum import Enum
from typing_extensions import Annotated

from pydantic_mongo import ObjectIdField, EnumAnnotation


class User(BaseModel):
    id: ObjectIdField


class State(Enum):
    Preparation = "Preparation"
    Processing = "Processing"


class Order(BaseModel):
    state: Annotated[State, EnumAnnotation[State]]


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
        dump = user.model_dump_json()
        assert '{"id":"611827f2878b88b49ebb69fc"}' == dump


    def test_object_id_field_dump(self):
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        dump = user.model_dump(mode="python")
        assert {"id": ObjectId("611827f2878b88b49ebb69fc")} == dump
        dump = user.model_dump(mode="json")
        assert {"id": "611827f2878b88b49ebb69fc"} == dump


    def test_object_id_field_conversion(self):
        user = User(id="611827f2878b88b49ebb69fc")
        assert user.id == ObjectId("611827f2878b88b49ebb69fc")


    def test_enum_field_dump(self):
        order = Order(state=State.Preparation)
        python_dump = order.model_dump(mode="python")
        json_dump = order.model_dump(mode="json")
        assert python_dump == {"state": "Preparation"}
        assert json_dump == {"state": "Preparation"}


    def test_enum_field_conversion(self):
        order = Order(state="Preparation")
        assert order.state == State.Preparation
        order = Order(state=State.Preparation)
        assert order.state == State.Preparation

    def test_enum_field_validation(self):
        with pytest.raises(ValidationError):
            Order(state="lala")
        Order(state=State.Preparation)  # Should not raise

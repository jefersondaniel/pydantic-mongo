import pytest
from bson import ObjectId
from pydantic import BaseModel, ValidationError

from pydantic_mongo import ObjectIdField


class User(BaseModel):
    id: ObjectIdField


class TestFields:
    def test_model_validate(self):
        with pytest.raises(ValidationError):
            User.model_validate({"id": "lala"})
        User.model_validate({"id": "611827f2878b88b49ebb69fc"})
        User.model_validate({"id": ObjectId("611827f2878b88b49ebb69fc")})

    def test_model_json_schema(self):
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        schema = user.model_json_schema()
        assert {
            "title": "User",
            "type": "object",
            "properties": {"id": {"title": "Id", "type": "string"}},
            "required": ["id"],
        } == schema

    def test_model_dump_json(self):
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        dump = user.model_dump_json()
        assert '{"id":"611827f2878b88b49ebb69fc"}' == dump

    def test_model_dump(self):
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        dump = user.model_dump(mode="python")
        assert {"id": ObjectId("611827f2878b88b49ebb69fc")} == dump
        dump = user.model_dump(mode="json")
        assert {"id": "611827f2878b88b49ebb69fc"} == dump

    def test_field_conversion(self):
        user = User(id="611827f2878b88b49ebb69fc")
        assert user.id == ObjectId("611827f2878b88b49ebb69fc")

import pytest
from bson import ObjectId
from pydantic import BaseModel, ValidationError

from pydantic_mongo import ObjectIdField


class User(BaseModel):
    id: ObjectIdField = None


class TestFields:
    def test_object_id_validation(self):
        with pytest.raises(ValidationError):
            User.model_validate({"id": "lala"})
        User.model_validate({"id": "611827f2878b88b49ebb69fc"})

    def test_object_id_serialize(self):
        lala = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        json_result = lala.model_dump_json()
        assert '{"id":"611827f2878b88b49ebb69fc"}' == json_result

    def test_modify_schema(self):
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))
        schema = user.model_json_schema()
        assert {
            "title": "User",
            "type": "object",
            "properties": {"id": {"default": None, "title": "Id", "type": "string"}},
        } == schema

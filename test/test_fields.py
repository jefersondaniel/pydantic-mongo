import pytest
from bson import ObjectId
from pydantic_mongo import ObjectIdField
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError


class User(BaseModel):
    id: ObjectIdField = None

    class Config:
        json_encoders = {ObjectId: str}


class TestFields:
    def test_object_id_validation(self):
        with pytest.raises(ValidationError):
            User.parse_obj({'id': 'lala'})
        User.parse_obj({'id': '611827f2878b88b49ebb69fc'})

    def test_object_id_serialize(self):
        lala = User(id=ObjectId('611827f2878b88b49ebb69fc'))
        json_result = lala.json()
        assert '{"id": "611827f2878b88b49ebb69fc"}' == json_result

    def test_modify_schema(self):
        user = User(id=ObjectId('611827f2878b88b49ebb69fc'))
        schema = user.schema()
        assert {
            'title': 'User',
            'type': 'object',
            'properties': {
                'id': {
                    'title': 'Id',
                    'type': 'string'
                }
            }
        } == schema

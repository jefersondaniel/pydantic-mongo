from bson import ObjectId


class ObjectIdField:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid id")

        return ObjectId(value)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

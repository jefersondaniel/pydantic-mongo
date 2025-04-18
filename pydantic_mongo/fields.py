from enum import Enum
from typing import Any, Generic, TypeVar

from bson import ObjectId
from pydantic import BaseModel
from pydantic_core import core_schema
from typing_extensions import Annotated

TEnum = TypeVar("TEnum", bound=Enum)


class EnumAnnotation(BaseModel, Generic[TEnum]):
    """A Pydantic annotation for Enum fields."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any):
        # Create a schema that validates and converts strings to the enum class
        enum_type = _source_type

        enum_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(
                    lambda value: cls.validate_enum(value, enum_type)
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            # For JSON, we'll use a string schema for serialization
            json_schema=core_schema.str_schema(),
            # For Python, we'll accept either an enum instance or a string that can be converted
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(enum_type), enum_schema]
            ),
            # Always serialize to string
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: (
                    instance.value if isinstance(instance, Enum) else instance
                )
            ),
        )

    @classmethod
    def validate_enum(cls, value: Any, enum_type: type[TEnum]) -> TEnum:
        """Validate and convert a value to the Enum type.

        Args:
            value: The value to validate and convert
            enum_type: The Enum class to convert to

        Returns:
            The converted Enum instance

        Raises:
            ValueError: If the value doesn't match any enum values
        """
        try:
            # Try to find the enum by value
            return enum_type(value)
        except ValueError as err:
            # If we get here, no match was found
            valid_values = [e.value for e in enum_type]
            raise ValueError(
                f"Invalid value '{value}' for {enum_type.__name__}. "
                f"Valid values: {valid_values}"
            ) from err


class ObjectIdAnnotation:
    """A Pydantic annotation for MongoDB ObjectId fields.

    This annotation provides validation and serialization for MongoDB ObjectId fields
    in Pydantic models. It allows ObjectIds to be:

    - Created from string representations
    - Validated for correct ObjectId format
    - Serialized to string format for JSON output

    Example:

        .. code-block:: python

            from typing_extensions import Annotated
            from bson import ObjectId
            from pydantic import BaseModel
            from pydantic_mongo import ObjectIdAnnotation

            class User(BaseModel):
                # Using the annotation directly
                id: Annotated[ObjectId, ObjectIdAnnotation]

                # Or using the provided type alias
                id: PydanticObjectId  # equivalent to above

    When the model is loaded, strings will be automatically converted to ObjectId
    instances if they are valid, and an error will be raised if they are not.
    When the model is serialized to JSON, ObjectIds will be converted to strings.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        """Get the Pydantic core schema for ObjectId validation and serialization.

        This method is called by Pydantic to get the schema for validating and
        serializing ObjectId fields. It sets up:

        - String validation and conversion to ObjectId
        - Direct ObjectId instance validation
        - String serialization for JSON output

        Args:
            _source_type: The source type annotation (unused)
            _handler: The schema handler (unused)

        Returns:
            core_schema.CoreSchema: The schema for ObjectId fields
        """
        object_id_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]
        )
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(ObjectId), object_id_schema]
            ),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, value):
        """Validate and convert a string to ObjectId.

        Args:
            value: The string value to validate and convert

        Returns:
            ObjectId: The converted ObjectId instance

        Raises:
            ValueError: If the value is not a valid ObjectId string
        """
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid id")

        return ObjectId(value)


# Deprecated, use PydanticObjectId instead.
class ObjectIdField(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any):
        return ObjectIdAnnotation.__get_pydantic_core_schema__(_source_type, _handler)


PydanticObjectId = Annotated[ObjectId, ObjectIdAnnotation]
"""A type alias for MongoDB ObjectId fields in Pydantic models.

This type combines MongoDB's ObjectId with Pydantic validation and serialization.
It allows you to use ObjectId fields in your models with automatic validation
and conversion between string and ObjectId formats.

Example:

    .. code-block:: python

        from pydantic import BaseModel
        from pydantic_mongo import PydanticObjectId

        class User(BaseModel):
            id: PydanticObjectId

        # Create from string - automatically converts to ObjectId
        user = User(id="611827f2878b88b49ebb69fc")
        assert isinstance(user.id, ObjectId)

        # Create from ObjectId directly
        user = User(id=ObjectId("611827f2878b88b49ebb69fc"))

        # Invalid ObjectId strings raise ValidationError
        try:
            User(id="invalid")  # Raises ValidationError
        except ValidationError:
            pass

        # JSON serialization converts ObjectId to string
        user_json = user.model_dump_json()
        assert user_json == '{"id":"611827f2878b88b49ebb69fc"}'

        # Python dict serialization keeps ObjectId
        user_dict = user.model_dump(mode="python")
        assert isinstance(user_dict["id"], ObjectId)

        # JSON dict serialization converts to string
        user_json_dict = user.model_dump(mode="json")
        assert isinstance(user_json_dict["id"], str)
"""

from __future__ import annotations
import enum
from typing import Optional, List
from pydantic import BaseModel
from pydantic_mongo.enum import get_enum_types_in_model, get_type_registry
from bson.codec_options import CodecOptions
from bson import BSON


class Color(enum.Enum):
    RED = "red"
    BLUE = "blue"


class MyInnerEnum(str, enum.Enum):
    FOO = "foo"
    BAR = "bar"


class ChildModel(BaseModel):
    color: Color
    maybe_enum: Optional[MyInnerEnum]


class ParentModel(BaseModel):
    child: ChildModel
    tags: List[MyInnerEnum]


class Node(BaseModel):
    value: 'Node'
    color: Color
    parent: Optional['Node'] = None


class TestEnum:
    def test_construct_type_registry(self):
        registry = get_type_registry(ParentModel)
        codec_options = CodecOptions(type_registry=registry)
        assert codec_options is not None

    def test_get_enum_types_in_model(self):
        assert get_enum_types_in_model(ParentModel) == {Color, MyInnerEnum}

    def test_get_enum_types_in_recursive_model(self):
        assert get_enum_types_in_model(Node) == {Color}

    def test_bson_serialization(self):
        # Create a sample document with enums
        doc = ParentModel(
            child=ChildModel(
                color=Color.RED,
                maybe_enum=MyInnerEnum.FOO
            ),
            tags=[MyInnerEnum.FOO, MyInnerEnum.BAR]
        )

        # Create codec options using the type registry for ParentModel
        codec_options = CodecOptions(type_registry=get_type_registry(ParentModel))

        # Encode and decode document
        serialized = BSON.encode(doc.model_dump(), codec_options=codec_options)
        decoded = BSON(serialized).decode(codec_options=codec_options)

        # Assert that the enums are correctly deserialized
        assert isinstance(decoded["child"]["color"], Color)
        assert decoded["child"]["color"] == Color.RED
        assert isinstance(decoded["child"]["maybe_enum"], MyInnerEnum)
        assert decoded["child"]["maybe_enum"] == MyInnerEnum.FOO
        for item in decoded["tags"]:
            assert isinstance(item, MyInnerEnum)
        assert decoded["tags"] == [MyInnerEnum.FOO, MyInnerEnum.BAR]

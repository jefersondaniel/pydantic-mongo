import enum
import inspect
from typing import Set, Type, Union, Any, get_args, get_origin

from pydantic import BaseModel
from bson.codec_options import TypeCodec, TypeRegistry


def _collect_enums_from_type(t: Any,
                             visited: Set[Type[enum.Enum]],
                             visited_models: Set[Type[BaseModel]] = None) -> None:
    if visited_models is None:
        visited_models = set()

    origin = get_origin(t)
    if origin is Union:
        for arg in get_args(t):
            _collect_enums_from_type(arg, visited, visited_models)
        return

    if origin in (list, set, tuple, dict):
        for arg in get_args(t):
            _collect_enums_from_type(arg, visited, visited_models)
        return

    if inspect.isclass(t) and issubclass(t, enum.Enum):
        visited.add(t)
        return

    if inspect.isclass(t) and issubclass(t, BaseModel):
        if t in visited_models:
            return
        visited_models.add(t)
        for f in t.model_fields.values():
            _collect_enums_from_type(f.annotation, visited, visited_models)


def _collect_enums_from_model(model: Type[BaseModel],
                              visited: Set[Type[enum.Enum]],
                              visited_models: Set[Type[BaseModel]] = None) -> None:
    if visited_models is None:
        visited_models = set()
    if model in visited_models:
        return
    visited_models.add(model)
    for field in model.model_fields.values():
        _collect_enums_from_type(field.annotation, visited, visited_models)


def get_enum_types_in_model(model_cls: Type[BaseModel]) -> Set[Type[enum.Enum]]:
    visited_enums: Set[Type[enum.Enum]] = set()
    visited_models: Set[Type[BaseModel]] = set()
    _collect_enums_from_model(model_cls, visited_enums, visited_models)
    return visited_enums


class EnumCodec(TypeCodec):
    bson_type = str

    def __init__(self, enum_cls: Type[enum.Enum]):
        self._enum_cls = enum_cls

    @property
    def python_type(self) -> Type[enum.Enum]:
        return self._enum_cls

    def transform_python(self, value: enum.Enum) -> str:
        return value.value

    def transform_bson(self, value: str) -> enum.Enum:
        if value not in self._enum_cls:
            raise ValueError(f"Enum value {value} not recognized by this codec.")
        return self._enum_cls(value)

    def __repr__(self) -> str:
        return f"EnumCodec({self._enum_cls})"


def get_type_registry(model_cls: Type[BaseModel]) -> TypeRegistry:
    discovered_enums = get_enum_types_in_model(model_cls)
    codecs = []

    for e in discovered_enums:
        if issubclass(e, str):
            continue
        codecs.append(EnumCodec(e))

    print(codecs)

    return TypeRegistry(codecs)

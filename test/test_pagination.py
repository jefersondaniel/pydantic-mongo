from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel

from pydantic_mongo.pagination import (
    decode_pagination_cursor,
    encode_pagination_cursor,
    get_pagination_cursor_payload,
)


class Foo(BaseModel):
    count: int
    size: Optional[float] = None


class Bar(BaseModel):
    apple: str = "x"
    banana: str = "y"


class Spam(BaseModel):
    id: Optional[str] = None
    foo: Foo
    bars: List[Bar]


class TestPagination:
    def test_get_pagination_cursor_payload(self):
        spam = Spam(id="lala", foo=Foo(count=1, size=1.0), bars=[Bar()])

        values = get_pagination_cursor_payload(spam, ["_id", "id"])
        assert values[0] == "lala"
        assert values[1] == "lala"

        values = get_pagination_cursor_payload(spam, ["foo.count"])
        assert values[0] == 1

        values = get_pagination_cursor_payload(spam, ["bars.0.apple"])
        assert values[0] == "x"

    def test_cursor_encoding(self):
        old_value = [ObjectId("611b158adec89d18984b7d90"), "a", 1]
        cursor = encode_pagination_cursor(old_value)
        new_value = decode_pagination_cursor(cursor)
        assert old_value == new_value

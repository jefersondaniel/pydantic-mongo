from typing import List

import mongomock
import pytest
from bson import ObjectId
from pydantic import BaseModel, Field

from pydantic_mongo import AbstractRepository, ObjectIdField
from pydantic_mongo.errors import PaginationError


class Foo(BaseModel):
    count: int
    size: float = None


class Bar(BaseModel):
    apple: str = Field(default="x")
    banana: str = Field(default="y")


class Spam(BaseModel):
    id: ObjectIdField = None
    foo: Foo = None
    bars: List[Bar] = None


class SpamRepository(AbstractRepository[Spam]):
    class Meta:
        collection_name = "spams"


@pytest.fixture
def database():
    return mongomock.MongoClient().db


class TestRepository:
    def test_save(self, database):
        spam_repository = SpamRepository(database=database)
        foo = Foo(count=1, size=1.0)
        bar = Bar()
        spam = Spam(foo=foo, bars=[bar])
        spam_repository.save(spam)

        assert {
            "_id": ObjectId(spam.id),
            "foo": {"count": 1, "size": 1.0},
            "bars": [{"apple": "x", "banana": "y"}],
        } == database["spams"].find()[0]

        spam.foo.count = 2
        spam_repository.save(spam)

        assert {
            "_id": ObjectId(spam.id),
            "foo": {"count": 2, "size": 1.0},
            "bars": [{"apple": "x", "banana": "y"}],
        } == database["spams"].find()[0]

    def test_save_upsert(self, database):
        spam_repository = SpamRepository(database=database)
        spam = Spam(
            id=ObjectId("65012da68ea5a4798502f710"),
            foo=Foo(count=1, size=1.0),
            bars=[]
        )
        spam_repository.save(spam)

        assert {
            "_id": ObjectId(spam.id),
            "foo": {"count": 1, "size": 1.0},
            "bars": [],
        } == database["spams"].find()[0]

    def test_save_many(self, database):
        spam_repository = SpamRepository(database=database)
        spams = [
            Spam(),
            Spam(id=ObjectId("65012da68ea5a4798502f710")),
        ]
        spam_repository.save_many(spams)

        initial_data = [
            {
                "_id": ObjectId(spams[0].id),
                "foo": None,
                "bars": None,
            },
            {
                "_id": ObjectId(spams[1].id),
                "foo": None,
                "bars": None,
            },
        ]

        assert initial_data == list(database["spams"].find())

        # Calling save_many again will only update
        spam_repository.save_many(spams)
        assert initial_data == list(database["spams"].find())

        # Calling save_many with only a new model will only insert
        new_span = Spam()
        spam_repository.save_many([new_span])
        assert new_span.id is not None
        assert 3 == database["spams"].count_documents({})

    def test_delete(self, database):
        spam_repository = SpamRepository(database=database)
        foo = Foo(count=1, size=1.0)
        bar = Bar()
        spam = Spam(foo=foo, bars=[bar])
        spam_repository.save(spam)

        result = spam_repository.find_one_by_id(spam.id)
        assert result is not None

        spam_repository.delete(spam)
        result = spam_repository.find_one_by_id(spam.id)
        assert result is None

    def test_delete_by_id(self, database):
        spam_repository = SpamRepository(database=database)
        foo = Foo(count=1, size=1.0)
        bar = Bar()
        spam = Spam(foo=foo, bars=[bar])
        spam_repository.save(spam)

        result = spam_repository.find_one_by_id(spam.id)
        assert result is not None

        spam_repository.delete_by_id(spam.id)
        result = spam_repository.find_one_by_id(spam.id)
        assert result is None

    def test_find_by_id(self, database):
        spam_id = ObjectId("611827f2878b88b49ebb69fc")
        database.spams.insert_one(
            {
                "_id": spam_id,
                "foo": {"count": 2, "size": 1.0},
                "bars": [{"apple": "x", "banana": "y"}],
            }
        )

        spam_repository = SpamRepository(database=database)
        result = spam_repository.find_one_by_id(spam_id)

        assert issubclass(Spam, type(result))
        assert spam_id == result.id
        assert "x" == result.bars[0].apple

    def test_find_by(self, database):
        database.spams.insert_many(
            [
                {
                    "foo": {"count": 2, "size": 1.0},
                    "bars": [{"apple": "x", "banana": "y"}],
                },
                {
                    "foo": {"count": 3, "size": 1.0},
                    "bars": [{"apple": "x", "banana": "y"}],
                },
            ]
        )

        spam_repository = SpamRepository(database=database)

        # Simple Find
        result = spam_repository.find_by({})
        results = [x for x in result]
        assert 2 == len(results)
        assert 2 == results[0].foo.count
        assert 3 == results[1].foo.count

        # Find with optional parameters
        result = spam_repository.find_by(
            {}, skip=10, limit=10, sort=[("foo.count", 1), ("id", 1)]
        )
        results = [x for x in result]
        assert 0 == len(results)

    def test_invalid_model_class(self, database):
        class BrokenRepository(AbstractRepository[int]):
            class Meta:
                collection_name = "spams"

        with pytest.raises(Exception):
            BrokenRepository(database=database)

    def test_invalid_model_id_field(self, database):
        class NoIdModel(BaseModel):
            something: str

        class BrokenRepository(AbstractRepository[NoIdModel]):
            class Meta:
                collection_name = "spams"

        with pytest.raises(Exception):
            BrokenRepository(database=database)

    def test_invalid_model_collection_name(self, database):
        class BrokenRepository(AbstractRepository[Spam]):
            class Meta:
                collection_name = None

        with pytest.raises(Exception):
            BrokenRepository(database=database)

    def test_paginate(self, database):
        database.spams.insert_many(
            [
                {
                    "_id": ObjectId("611b140f4eb6ee47e966860f"),
                    "foo": {"count": 2, "size": 1.0},
                    "bars": [{"apple": "x", "banana": "y"}],
                },
                {
                    "id": ObjectId("611b141cf533ca420b7580d6"),
                    "foo": {"count": 3, "size": 1.0},
                    "bars": [{"apple": "x", "banana": "y"}],
                },
                {
                    "_id": ObjectId("611b15241dea2ee3f7cbfe30"),
                    "foo": {"count": 2, "size": 1.0},
                    "bars": [{"apple": "x", "banana": "y"}],
                },
                {
                    "_id": ObjectId("611b157c859bde7de88c98ac"),
                    "foo": {"count": 2, "size": 1.0},
                    "bars": [{"apple": "x", "banana": "y"}],
                },
                {
                    "_id": ObjectId("611b158adec89d18984b7d90"),
                    "foo": {"count": 2, "size": 1.0},
                    "bars": [{"apple": "x", "banana": "y"}],
                },
            ]
        )

        spam_repository = SpamRepository(database=database)

        # Simple Find
        result = list(spam_repository.paginate({}, limit=10))
        assert len(result) == 5

        # Find After
        result = list(
            spam_repository.paginate(
                {}, limit=10, after="eNqTYWBgYCljEAFS7AYMidKiXfdOzJWY4V07gYEBAD7HBkg="
            )
        )
        assert len(result) == 1

        # Find Before
        result = list(
            spam_repository.paginate(
                {}, limit=10, before="eNqTYWBgYCljEAFS7AYMidKiXfdOzJWY4V07gYEBAD7HBkg="
            )
        )
        assert len(result) == 3

        with pytest.raises(PaginationError):
            spam_repository.paginate({}, limit=10, after="invalid string")

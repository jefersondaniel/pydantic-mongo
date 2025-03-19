from typing import List, Optional, cast

import pytest
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import AsyncMongoClient

from pydantic_mongo import AbstractRepository, PydanticObjectId
from pydantic_mongo.async_abstract_repository import AsyncAbstractRepository
from pydantic_mongo.errors import PaginationError


class Foo(BaseModel):
    count: int
    size: Optional[float] = None


class Bar(BaseModel):
    apple: str = Field(default="x")
    banana: str = Field(default="y")


class Spam(BaseModel):
    id: Optional[PydanticObjectId] = None
    foo: Optional[Foo] = None
    bars: Optional[List[Bar]] = None


class SpamRepository(AsyncAbstractRepository[Spam]):
    class Meta:
        collection_name = "spams"


@pytest.fixture
def database():
    import asyncio

    client: AsyncMongoClient = AsyncMongoClient("mongodb://localhost:27017")
    asyncio.run(client.drop_database("db"))

    return client.db


class TestAsyncRepository:
    @pytest.mark.asyncio
    async def test_save(self, database):
        spam_repository = SpamRepository(database=database)
        foo = Foo(count=1, size=1.0)
        bar = Bar()
        spam = Spam(foo=foo, bars=[bar])
        await spam_repository.save(spam)

        result = await database["spams"].find().to_list(length=None)
        assert {
            "_id": ObjectId(spam.id),
            "foo": {"count": 1, "size": 1.0},
            "bars": [{"apple": "x", "banana": "y"}],
        } == result[0]

        cast(Foo, spam.foo).count = 2
        await spam_repository.save(spam)

        result = await database["spams"].find().to_list(length=None)
        assert {
            "_id": ObjectId(spam.id),
            "foo": {"count": 2, "size": 1.0},
            "bars": [{"apple": "x", "banana": "y"}],
        } == result[0]

    @pytest.mark.asyncio
    async def test_save_upsert(self, database):
        spam_repository = SpamRepository(database=database)
        spam = Spam(
            id=ObjectId("65012da68ea5a4798502f710"), foo=Foo(count=1, size=1.0), bars=[]
        )
        await spam_repository.save(spam)

        result = await database["spams"].find().to_list(length=None)
        assert {
            "_id": ObjectId(spam.id),
            "foo": {"count": 1, "size": 1.0},
            "bars": [],
        } == result[0]

    @pytest.mark.asyncio
    async def test_save_many(self, database):
        spam_repository = SpamRepository(database=database)
        spams = [
            Spam(),
            Spam(id=ObjectId("65012da68ea5a4798502f710")),
        ]
        await spam_repository.save_many(spams)

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

        result = await database["spams"].find().to_list(length=None)
        assert initial_data == result

        # Calling save_many again will only update
        await spam_repository.save_many(spams)
        result = await database["spams"].find().to_list(length=None)
        assert initial_data == result

        # Calling save_many with only a new model will only insert
        new_span = Spam()
        await spam_repository.save_many([new_span])
        assert new_span.id is not None
        assert 3 == await database["spams"].count_documents({})

    @pytest.mark.asyncio
    async def test_delete(self, database):
        spam_repository = SpamRepository(database=database)
        foo = Foo(count=1, size=1.0)
        bar = Bar()
        spam = Spam(foo=foo, bars=[bar])
        await spam_repository.save(spam)

        result = await spam_repository.find_one_by_id(spam.id)
        assert result is not None

        await spam_repository.delete(spam)
        result = await spam_repository.find_one_by_id(spam.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_by_id(self, database):
        spam_repository = SpamRepository(database=database)
        foo = Foo(count=1, size=1.0)
        bar = Bar()
        spam = Spam(foo=foo, bars=[bar])
        await spam_repository.save(spam)

        result = await spam_repository.find_one_by_id(spam.id)
        assert result is not None

        await spam_repository.delete_by_id(spam.id)
        result = await spam_repository.find_one_by_id(spam.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_id(self, database):
        spam_id = ObjectId("611827f2878b88b49ebb69fc")
        await database["spams"].insert_one(
            {
                "_id": spam_id,
                "foo": {"count": 2, "size": 1.0},
                "bars": [{"apple": "x", "banana": "y"}],
            }
        )

        spam_repository = SpamRepository(database=database)
        result = await spam_repository.find_one_by_id(spam_id)

        assert result is not None
        assert result.bars is not None
        assert issubclass(Spam, type(result))
        assert spam_id == result.id
        assert "x" == result.bars[0].apple

    @pytest.mark.asyncio
    async def test_find_by(self, database):
        await database["spams"].insert_many(
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
        result = await spam_repository.find_by({})
        results = [x for x in result]
        assert 2 == len(results)
        assert results[0].foo is not None
        assert results[1].foo is not None
        assert 2 == results[0].foo.count
        assert 3 == results[1].foo.count

        # Find with optional parameters
        result = await spam_repository.find_by(
            {}, skip=10, limit=10, sort=[("foo.count", 1), ("id", 1)]
        )
        results = [x for x in result]
        assert 0 == len(results)

    @pytest.mark.asyncio
    async def test_invalid_model_id_field(self, database):
        class NoIdModel(BaseModel):
            something: str

        class BrokenRepository(AbstractRepository[NoIdModel]):
            class Meta:
                collection_name = "spams"

        with pytest.raises(Exception):
            BrokenRepository(database=database)

    @pytest.mark.asyncio
    async def test_invalid_model_collection_name(self, database):
        class BrokenRepository(AbstractRepository[Spam]):
            class Meta:
                collection_name = None

        with pytest.raises(Exception):
            BrokenRepository(database=database)

    @pytest.mark.asyncio
    async def test_paginate(self, database):
        await database["spams"].insert_many(
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
        result = list(await spam_repository.paginate({}, limit=10))
        assert len(result) == 5

        # Find After
        result = list(
            await spam_repository.paginate(
                {}, limit=10, after="eNqTYWBgYCljEAFS7AYMidKiXfdOzJWY4V07gYEBAD7HBkg="
            )
        )
        assert len(result) == 1

        # Find Before
        result = list(
            await spam_repository.paginate(
                {}, limit=10, before="eNqTYWBgYCljEAFS7AYMidKiXfdOzJWY4V07gYEBAD7HBkg="
            )
        )
        assert len(result) == 3

        with pytest.raises(PaginationError):
            await spam_repository.paginate({}, limit=10, after="invalid string")

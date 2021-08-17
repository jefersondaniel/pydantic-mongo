import pytest
import mongomock
from bson import ObjectId
from typing import List
from pydantic_mongo import AbstractRepository, ObjectIdField
from pydantic import BaseModel
from pydantic_mongo.errors import PaginationError


class Foo(BaseModel):
    count: int
    size: float = None


class Bar(BaseModel):
    apple = 'x'
    banana = 'y'


class Spam(BaseModel):
    id: ObjectIdField = None
    foo: Foo
    bars: List[Bar]

    class Config:
        json_encoders = {ObjectId: str}


class SpamRepository(AbstractRepository[Spam]):
    class Meta:
        collection_name = 'spams'


@pytest.fixture
def database():
    return mongomock.MongoClient().db.collection


class TestRepository:
    def test_save(self, database):
        spam_repository = SpamRepository(database=database)
        foo = Foo(count=1, size=1.0)
        bar = Bar()
        spam = Spam(foo=foo, bars=[bar])
        spam_repository.save(spam)

        assert {
            '_id': ObjectId(spam.id),
            'foo': {'count': 1, 'size': 1.0},
            'bars': [{'apple': 'x', 'banana': 'y'}]
        } == database['spams'].find()[0]

        spam.foo.count = 2
        spam_repository.save(spam)

        assert {
            '_id': ObjectId(spam.id),
            'foo': {'count': 2, 'size': 1.0},
            'bars': [{'apple': 'x', 'banana': 'y'}]
        } == database['spams'].find()[0]

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

    def test_find_by_id(self, database):
        spam_id = ObjectId('611827f2878b88b49ebb69fc')
        database.spams.insert_one({
            '_id': spam_id,
            'foo': {'count': 2, 'size': 1.0},
            'bars': [{'apple': 'x', 'banana': 'y'}]
        })

        spam_repository = SpamRepository(database=database)
        result = spam_repository.find_one_by_id(spam_id)

        assert issubclass(Spam, type(result))
        assert spam_id == result.id
        assert 'x' == result.bars[0].apple

    def test_find_by(self, database):
        database.spams.insert_many([
            {
                'foo': {'count': 2, 'size': 1.0},
                'bars': [{'apple': 'x', 'banana': 'y'}]
            },
            {
                'foo': {'count': 3, 'size': 1.0},
                'bars': [{'apple': 'x', 'banana': 'y'}]
            },
        ])

        spam_repository = SpamRepository(database=database)

        # Simple Find
        result = spam_repository.find_by({})
        results = [x for x in result]
        assert 2 == len(results)
        assert 2 == results[0].foo.count
        assert 3 == results[1].foo.count

        # Find with optional parameters
        result = spam_repository.find_by({}, skip=10, limit=10, sort=[('foo.count', 1), ('id', 1)])
        results = [x for x in result]
        assert 0 == len(results)

    def test_invalid_model_class(self, database):
        class BrokenRepository(AbstractRepository[int]):
            class Meta:
                collection_name = 'spams'
        with pytest.raises(Exception):
            BrokenRepository(database=database)

    def test_invalid_model_id_field(self, database):
        class NoIdModel(BaseModel):
            something: str

        class BrokenRepository(AbstractRepository[NoIdModel]):
            class Meta:
                collection_name = 'spams'

        with pytest.raises(Exception):
            BrokenRepository(database=database)

    def test_invalid_model_collection_name(self, database):
        class BrokenRepository(AbstractRepository[Spam]):
            class Meta:
                collection_name = None

        with pytest.raises(Exception):
            BrokenRepository(database=database)

    def test_paginate(self, database):
        database.spams.insert_many([
            {
                '_id': ObjectId('611b140f4eb6ee47e966860f'),
                'foo': {'count': 2, 'size': 1.0},
                'bars': [{'apple': 'x', 'banana': 'y'}]
            },
            {
                'id': ObjectId('611b141cf533ca420b7580d6'),
                'foo': {'count': 3, 'size': 1.0},
                'bars': [{'apple': 'x', 'banana': 'y'}]
            },
            {
                '_id': ObjectId('611b15241dea2ee3f7cbfe30'),
                'foo': {'count': 2, 'size': 1.0},
                'bars': [{'apple': 'x', 'banana': 'y'}]
            },
            {
                '_id': ObjectId('611b157c859bde7de88c98ac'),
                'foo': {'count': 2, 'size': 1.0},
                'bars': [{'apple': 'x', 'banana': 'y'}]
            },
            {
                '_id': ObjectId('611b158adec89d18984b7d90'),
                'foo': {'count': 2, 'size': 1.0},
                'bars': [{'apple': 'x', 'banana': 'y'}]
            },
        ])

        spam_repository = SpamRepository(database=database)

        # Simple Find
        result = list(spam_repository.paginate({}, limit=10))
        assert len(result) == 5

        # Find After
        result = list(spam_repository.paginate({}, limit=10, after='eNqTYWBgYCljEAFS7AYMidKiXfdOzJWY4V07gYEBAD7HBkg='))
        assert len(result) == 1

        # Find Before
        result = list(spam_repository.paginate({}, limit=10, before='eNqTYWBgYCljEAFS7AYMidKiXfdOzJWY4V07gYEBAD7HBkg='))
        assert len(result) == 3

        with pytest.raises(PaginationError):
            spam_repository.paginate({}, limit=10, after='invalid string')

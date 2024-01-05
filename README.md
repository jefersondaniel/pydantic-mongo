# Pydantic Mongo

[![Build Status](https://github.com/jefersondaniel/pydantic-mongo/actions/workflows/test.yml/badge.svg)](https://github.com/jefersondaniel/pydantic-mongo/actions) [![Maintainability](https://api.codeclimate.com/v1/badges/5c92ea54aefa29f919cf/maintainability)](https://codeclimate.com/github/jefersondaniel/pydantic-mongo/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/5c92ea54aefa29f919cf/test_coverage)](https://codeclimate.com/github/jefersondaniel/pydantic-mongo/test_coverage) [![Version](https://badge.fury.io/py/pydantic-mongo.svg)](https://pypi.python.org/pypi/pydantic-mongo) [![Downloads](https://img.shields.io/pypi/dm/pydantic-mongo.svg)](https://pypi.python.org/pypi/pydantic-mongo)

Document object mapper for pydantic and pymongo

## Usage

### Install:

```bash
pip install pydantic-mongo
```

### Example Code

```python
from bson import ObjectId
from pydantic import BaseModel
from pydantic_mongo import AbstractRepository, ObjectIdField
from pymongo import MongoClient
from typing import List
import os

class Foo(BaseModel):
   count: int
   size: float = None

class Bar(BaseModel):
   apple: str = 'x'
   banana: str = 'y'

class Spam(BaseModel):
   id: ObjectIdField = None
   foo: Foo
   bars: List[Bar]

class SpamRepository(AbstractRepository[Spam]):
   class Meta:
      collection_name = 'spams'

client = MongoClient("mongodb://localhost:27017")
database = client["example"]

spam = Spam(foo=Foo(count=1, size=1.0),bars=[Bar()])

spam_with_predefined_id = Spam(
   id=ObjectId("611827f2878b88b49ebb69fc"),
   foo=Foo(count=2, size=2.0),
   bars=[Bar()]
)

spam_repository = SpamRepository(database=database)

# Insert / Update
spam_repository.save(spam)

# Insert / Update many items
spam_repository.save_many([spam, spam_with_predefined_id])

# Delete
spam_repository.delete(spam)

# Find One By Id
result = spam_repository.find_one_by_id(spam.id)

# Find One By Id using string if the id attribute is a ObjectIdField
result = spam_repository.find_one_by_id(ObjectId('611827f2878b88b49ebb69fc'))
assert result.foo.count == 2

# Find One By Query
result = spam_repository.find_one_by({'foo.count': 1})

# Find By Query
results = spam_repository.find_by({'foo.count': {'$gte': 1}})

# Paginate using cursor based pagination
edges = spam_repository.paginate({'foo.count': {'$gte': 1}}, limit=1)
more_edges = spam_repository.paginate({'foo.count': {'$gte': 1}}, limit=1, after=list(edges)[-1].cursor)
```

# Pydantic Mongo

[![Build Status](https://github.com/jefersondaniel/pydantic-mongo/actions/workflows/test.yml/badge.svg)](https://github.com/jefersondaniel/pydantic-mongo/actions) 
[![Maintainability](https://api.codeclimate.com/v1/badges/5c92ea54aefa29f919cf/maintainability)](https://codeclimate.com/github/jefersondaniel/pydantic-mongo/maintainability) 
[![Test Coverage](https://api.codeclimate.com/v1/badges/5c92ea54aefa29f919cf/test_coverage)](https://codeclimate.com/github/jefersondaniel/pydantic-mongo/test_coverage) 
[![Version](https://badge.fury.io/py/pydantic-mongo.svg)](https://pypi.python.org/pypi/pydantic-mongo) 
[![Downloads](https://img.shields.io/pypi/dm/pydantic-mongo.svg)](https://pypi.python.org/pypi/pydantic-mongo)
[![Documentation Status](https://readthedocs.org/projects/pydantic-mongo/badge/?version=latest)](https://pydantic-mongo.readthedocs.io/en/latest/?badge=latest)

A Python library that provides an asynchronous and synchronous Abstract Repository pattern for MongoDB using Pydantic models. It simplifies database interactions by offering a high-level interface for CRUD operations while leveraging Pydantic's data validation and serialization capabilities. Easily manage your MongoDB data with type safety and structure, and extend the repositories for custom queries, aggregations, and projections.

[Read the documentation](https://pydantic-mongo.readthedocs.io/)

## Features

- Type-safe MongoDB operations
- Synchronous and asynchronous support
- Pydantic models integration
- Cursor-based pagination
- Customizable document transformations

## Installation

```bash
pip install pydantic-mongo
```

## Usage Examples

### Defining Models and Repository

```python
from bson import ObjectId
from pydantic import BaseModel
from pydantic_mongo import AbstractRepository, PydanticObjectId
from pymongo import MongoClient
from typing import Optional, List

# Define your models
class Foo(BaseModel):
   count: int
   size: float = None

class Bar(BaseModel):
   apple: str = 'x'
   banana: str = 'y'

class Spam(BaseModel):
   # PydanticObjectId is an alias to Annotated[ObjectId, ObjectIdAnnotation]
   id: Optional[PydanticObjectId] = None
   foo: Foo
   bars: List[Bar]

# Create a repository
class SpamRepository(AbstractRepository[Spam]):
   class Meta:
      collection_name = 'spams'

# Connect to database
client = MongoClient("mongodb://localhost:27017")
database = client["example"]
repo = SpamRepository(database)
```

### Creating and Saving Documents

```python
# Create a new document
spam = Spam(foo=Foo(count=1, size=1.0), bars=[Bar()])

# Create a document with predefined ID
spam_with_predefined_id = Spam(
   id=ObjectId("611827f2878b88b49ebb69fc"),
   foo=Foo(count=2, size=2.0),
   bars=[Bar()]
)

# Save a single document
repo.save(spam)  # spam.id is now set to an ObjectId

# Save multiple documents
repo.save_many([spam, spam_with_predefined_id])
```

### Querying Documents

```python
# Find by ID
result = repo.find_one_by_id(spam.id)

# Find by ID using string
result = repo.find_one_by_id(ObjectId('611827f2878b88b49ebb69fc'))
assert result.foo.count == 2

# Find one by custom query
result = repo.find_one_by({'foo.count': 1})

# Find multiple documents by query
results = repo.find_by({'foo.count': {'$gte': 1}})
```

### Pagination

```python
# Get first page
edges = repo.paginate({'foo.count': {'$gte': 1}}, limit=10)

# Get next page using the last cursor
more_edges = repo.paginate(
    {'foo.count': {'$gte': 1}}, 
    limit=10, 
    after=list(edges)[-1].cursor
)
```

### Deleting Documents

```python
# Delete a document
repo.delete(spam)

# Delete by ID
repo.delete_by_id(ObjectId("..."))
```

### Async Support

For asynchronous applications, you can use `AsyncAbstractRepository` which provides the same functionality as `AbstractRepository` but with async/await support:

```python
from pydantic_mongo import AsyncAbstractRepository
from motor.motor_asyncio import AsyncIOMotorClient

# Create async repository
class AsyncSpamRepository(AsyncAbstractRepository[Spam]):
   class Meta:
      collection_name = 'spams'

# Connect to database
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["example"]
async_repo = AsyncSpamRepository(database)

# Use with async/await
async def example():
    spam = Spam(foo=Foo(count=1), bars=[Bar()])
    await async_repo.save(spam)
    result = await async_repo.find_one_by_id(spam.id)
    print(result)
```

## License

MIT License

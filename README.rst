Pydantic Mongo
======================================

|Build Status| |Maintainability| |Test Coverage| |Version| |Pyversions|

Document object mapper for pydantic and pymongo

Documentation
~~~~~~~~~~~~~

Usage
^^^^^

Install:
''''''''

.. code:: bash

   $ pip install pydantic-mongo

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code:: python

    from pydantic import BaseModel
    from pydantic_mongo import AbstractRepository, ObjectIdField
    from pymongo import MongoClient

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
            # The ObjectIdField creates an bson ObjectId value, so its necessary to setup the json encoding
            json_encoders = {ObjectId: str}

    class SpamRepository(AbstractRepository[Spam]):
        class Meta:
            collection_name = 'spams'

    client = MongoClient(os.environ["MONGODB_URL"])
    database = client[os.environ["MONGODB_DATABASE"]]

    spam = Spam(foo=Foo(count=1, size=1.0),bars=[Bar()])

    spam_repository = SpamRepository(database=database)

    # Insert / Update
    spam_repository.save(spam)

    # Delete
    spam_repository.delete(spam)

    # Find One By Id
    result = spam_repository.find_one_by_id(spam.id)

    # Find One By Id using string if the id attribute is a ObjectIdField
    result = spam_repository.find_one_by_id(ObjectId('611827f2878b88b49ebb69fc'))

    # Find One By Query
    result = spam_repository.find_one_by({'foo.count': 1})

    # Find By Query
    results = spam_repository.find_by({'foo.count': {'$gte': 1}})

''''

.. |Build Status| image:: https://github.com/jefersondaniel/pydantic-mongo/actions/workflows/test.yml/badge.svg
   :target: https://github.com/jefersondaniel/pydantic-mongo/actions

.. |Maintainability| image:: https://api.codeclimate.com/v1/badges/5c92ea54aefa29f919cf/maintainability
   :target: https://codeclimate.com/github/jefersondaniel/pydantic-mongo/maintainability

.. |Test Coverage| image:: https://api.codeclimate.com/v1/badges/5c92ea54aefa29f919cf/test_coverage
   :target: https://codeclimate.com/github/jefersondaniel/pydantic-mongo/test_coverage

.. |Version| image:: https://badge.fury.io/py/pydantic-mongo.svg
   :target: https://pypi.python.org/pypi/pydantic-mongo

.. |Pyversions| image:: https://img.shields.io/pypi/pyversions/pydantic-mongo.svg
   :target: https://pypi.python.org/pypi/pydantic-mongo

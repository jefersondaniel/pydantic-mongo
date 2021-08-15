Pydantic Mongo
======================================

|Build Status| |Version| |Pyversions|

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

    # Find One By Query
    result = spam_repository.find_one_by({'foo.count': 1})

    # Find By Query
    results = spam_repository.find_by({'foo.count': {'$gte': 1}})

''''

.. |Build Status| image:: https://travis-ci.org/jefersondaniel/pydantic-mongo.svg
   :target: https://travis-ci.org/jefersondaniel/pydantic-mongo

.. |Version| image:: https://badge.fury.io/py/pydantic-mongo.svg
   :target: https://pypi.python.org/pypi/pydantic-mongo

.. |Pyversions| image:: https://img.shields.io/pypi/pyversions/pydantic-mongo.svg
   :target: https://pypi.python.org/pypi/pydantic-mongo

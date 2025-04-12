Quickstart
==========

Installation
------------

Install pydantic-mongo using pip:

.. code-block:: bash

    pip install pydantic-mongo

Basic Operations
----------------

Creating and Saving Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from bson import ObjectId
    from pydantic import BaseModel
    from pydantic_mongo import AbstractRepository, PydanticObjectId

    class User(BaseModel):
        id: PydanticObjectId = None
        name: str
        email: str

    class UserRepository(AbstractRepository[User]):
        class Meta:
            collection_name = 'users'

    # Create a new user
    user = User(name="John Doe", email="john@example.com")
    repo.save(user)  # user.id is now set to an ObjectId

Querying Documents
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Find by ID
    user = repo.find_one_by_id(ObjectId("..."))

    # Find by query
    active_users = repo.find_by({"status": "active"})

Pagination
~~~~~~~~~~

.. code-block:: python

    # Get first page
    edges = repo.paginate({"status": "active"}, limit=10)

    # Get next page using the last cursor
    next_edges = repo.paginate(
        {"status": "active"},
        limit=10,
        after=list(edges)[-1].cursor
    )

Deleting Documents
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Delete by model instance
    repo.delete(user)

    # Delete by ID
    repo.delete_by_id(ObjectId("..."))

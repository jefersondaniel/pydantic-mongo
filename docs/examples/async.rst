Async support
=============

This section describes how to use pydantic-mongo with asynchronous MongoDB operations.

.. code-block:: python

    from pymongo import AsyncMongoClient
    from pydantic import BaseModel
    from pydantic_mongo import AsyncAbstractRepository

    class User(BaseModel):
        id: str
        name: str
        email: str

    class UserRepository(AsyncAbstractRepository[User]):
        class Meta:
            collection_name = 'users'

    # Initialize database connection
    database = AsyncMongoClient('mongodb://localhost:27017/mydb')

    # Create repository instance
    user_repo = UserRepository(database)

    # Example usage
    async def create_user():
        user = User(name='John Doe', email='john@example.com')
        await user_repo.save(user)

    async def find_user(user_id: str):
        user = await user_repo.find_one_by_id(user_id)
        return user

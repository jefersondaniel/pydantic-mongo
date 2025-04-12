Using aggregations
==================

Aggregations allow for more complex queries and data processing. You can use the ``get_collection()`` method to access the underlying PyMongo collection and perform raw aggregation operations, then map the results to a custom model.

.. code-block:: python

    from pydantic import BaseModel
    from pydantic_mongo import AbstractRepository

    # Custom model for aggregation results
    class UserStats(BaseModel):
        role: str
        average_age: float
        total_count: int

    class UserRepository(AbstractRepository[User]):
        class Meta:
            collection_name = 'users'

        def get_user_stats(self) -> list[UserStats]:
            """Get statistics about users grouped by role."""
            pipeline = [
                {"$group": {
                    "_id": "$role",
                    "average_age": {"$avg": "$age"},
                    "total_count": {"$sum": 1}
                }},
                {"$project": {
                    "role": "$_id",
                    "average_age": 1,
                    "total_count": 1,
                    "_id": 0
                }}
            ]
            collection = self.get_collection()
            results = collection.aggregate(pipeline)
            return [UserStats(**doc) for doc in results]

    # Use the custom method
    repo = UserRepository(database)
    stats = repo.get_user_stats()
    for stat in stats:
        print(f"Role: {stat.role}, Avg Age: {stat.average_age}, Count: {stat.total_count}")

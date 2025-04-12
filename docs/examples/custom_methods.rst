Custom methods
==============

The ``get_collection()`` method provides direct access to the underlying PyMongo collection, allowing you to perform any raw MongoDB operation. Additionally, methods like ``find_by_with_output_type()`` and ``to_model_custom()`` enable you to extend the repository with custom logic for queries and data transformation.

This flexibility means you can implement any custom functionality needed for your application, such as custom queries, bulk operations, or specialized data processing, while still benefiting from Pydantic's type safety and validation.

**Converting PyMongo Output with ID Mapping**

The ``to_model_custom()`` and ``to_model()`` methods are particularly useful for converting raw PyMongo output to Pydantic models. These methods handle the mapping of MongoDB's ``_id`` field to the Pydantic model's ``id`` field, ensuring seamless integration between MongoDB data and your application logic.

.. code-block:: python

    class UserRepository(AbstractRepository[User]):
        class Meta:
            collection_name = 'users'

        def find_users_by_domain(self, domain: str) -> Iterable[User]:
            """Custom method to find users by email domain."""
            return self.find_by({"email": {"$regex": f"@{domain}$"}})

        def bulk_update_status(self, status: str, user_ids: list):
            """Custom method to update status for multiple users."""
            collection = self.get_collection()
            collection.update_many(
                {"_id": {"$in": user_ids}},
                {"$set": {"status": status}}
            )

        def get_user_by_raw_query(self, user_id: str) -> Optional[User]:
            """Custom method to fetch a user with raw PyMongo query and convert to model."""
            collection = self.get_collection()
            raw_data = collection.find_one({"_id": ObjectId(user_id)})
            return self.to_model(raw_data) if raw_data else None

        def get_custom_user_view(self, user_id: str) -> Optional[UserProfile]:
            """Custom method to fetch a user with raw PyMongo query and convert to a custom model."""
            collection = self.get_collection()
            raw_data = collection.find_one(
                {"_id": ObjectId(user_id)},
                projection={"name": 1, "age": 1, "_id": 0}
            )
            return self.to_model_custom(UserProfile, raw_data) if raw_data else None

    # Use custom methods
    repo = UserRepository(database)
    domain_users = repo.find_users_by_domain("example.com")
    repo.bulk_update_status("active", user_ids)
    user = repo.get_user_by_raw_query("valid-object-id")
    user_profile = repo.get_custom_user_view("valid-object-id")

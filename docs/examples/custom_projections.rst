Custom projections
==================

You can use custom projections with custom models to retrieve specific fields from your MongoDB collection and map them to a different Pydantic model than the one used in the repository. This is useful for creating view-specific models or reducing the amount of data transferred.

.. code-block:: python

    from pydantic import BaseModel
    from pydantic_mongo import AbstractRepository

    # Original model
    class User(BaseModel):
        id: PydanticObjectId = None
        name: str
        email: str
        age: int
        role: str

    # Custom model for projection (e.g., for a public profile view)
    class UserProfile(BaseModel):
        name: str
        age: int

    class UserRepository(AbstractRepository[User]):
        class Meta:
            collection_name = 'users'

        def find_profiles_by_role(self, role: str) -> Iterable[UserProfile]:
            """Find user profiles by role with a custom projection."""
            return self.find_by_with_output_type(
                output_type=UserProfile,
                query={"role": role},
                projection={"name": 1, "age": 1, "_id": 0}
            )

    # Use the custom method
    repo = UserRepository(database)
    profiles = repo.find_profiles_by_role("developer")
    for profile in profiles:
        print(profile)  # Only name and age fields are included

from typing import Any, Dict, Iterable, Optional, Type, Union, cast

from pymongo import UpdateOne
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.results import InsertOneResult, UpdateResult

from .base_abstract_repository import (
    BaseAbstractRepository,
    ModelWithId,
    OutputT,
    Sort,
    T,
)
from .pagination import Edge, encode_pagination_cursor, get_pagination_cursor_payload


class AsyncAbstractRepository(BaseAbstractRepository[T]):
    """An asynchronous repository implementation for MongoDB using Pydantic models.

    This class provides a high-level interface for performing asynchronous CRUD operations
    on MongoDB collections using Pydantic models for type safety and data validation.

    Example:
        class UserRepository(AsyncAbstractRepository[User]):
            class Meta:
                collection_name = 'users'

        repo = UserRepository(database)
        user = await repo.find_one_by_id(user_id)

    Generic type T must be a Pydantic model with an 'id' field.
    """

    class Meta:
        collection_name: str

    def __init__(self, database: AsyncDatabase):
        """Initialize the repository with an async MongoDB database connection.

        Args:
            database: PyMongo AsyncDatabase instance
        """
        self.__database: AsyncDatabase = database
        super().__init__()

    def get_collection(self) -> AsyncCollection:
        """Get the MongoDB collection associated with this repository.

        Returns:
            AsyncCollection: PyMongo AsyncCollection instance
        """
        return self.__database[self._collection_name]

    async def save(self, model: T) -> Union[InsertOneResult, UpdateResult]:
        """Asynchronously save a model instance to the database.

        This method will:
        - Insert the model if it doesn't have an ID
        - Update the model if it has an ID

        Args:
            model: The model instance to save

        Returns:
            Union[InsertOneResult, UpdateResult]: The result of the save operation
        """
        document = self.to_document(model)
        model_with_id = cast(ModelWithId, model)

        if model_with_id.id:
            mongo_id = document.pop("_id")
            return await self.get_collection().update_one(
                {"_id": mongo_id}, {"$set": document}, upsert=True
            )

        result = await self.get_collection().insert_one(document)
        model_with_id.id = result.inserted_id
        return result

    async def save_many(self, models: Iterable[T]):
        """Asynchronously save multiple model instances to the database in bulk.

        This method optimizes bulk operations by:
        - Grouping models into insert and update operations
        - Performing bulk inserts and updates

        Args:
            models: Iterable of model instances to save
        """
        models_to_insert = []
        models_to_update = []

        for model in models:
            model_with_id = cast(ModelWithId, model)
            if model_with_id.id:
                models_to_update.append(model)
            else:
                models_to_insert.append(model)
        if len(models_to_insert) > 0:
            result = await self.get_collection().insert_many(
                (self.to_document(model) for model in models_to_insert)
            )

            for idx, inserted_id in enumerate(result.inserted_ids):
                cast(ModelWithId, models_to_insert[idx]).id = inserted_id

        if len(models_to_update) == 0:
            return

        documents_to_update = [self.to_document(model) for model in models_to_update]
        mongo_ids = [doc.pop("_id") for doc in documents_to_update]
        bulk_operations = [
            UpdateOne({"_id": mongo_id}, {"$set": document}, upsert=True)
            for mongo_id, document in zip(mongo_ids, documents_to_update)
        ]
        await self.get_collection().bulk_write(bulk_operations)

    async def delete(self, model: T):
        """Asynchronously delete a model instance from the database.

        Args:
            model: The model instance to delete

        Returns:
            DeleteResult: The result of the delete operation
        """
        return await self.get_collection().delete_one(
            {"_id": cast(ModelWithId, model).id}
        )

    async def delete_by_id(self, _id: Any):
        """Asynchronously delete a model instance from the database by its ID.

        Args:
            _id: The ID of the model instance to delete

        Returns:
            DeleteResult: The result of the delete operation
        """
        return await self.get_collection().delete_one({"_id": _id})

    async def find_one_by_id(self, _id: Any) -> Optional[T]:
        """Asynchronously find a single model instance by its ID.

        Args:
            _id: The ID to search for. Must match the type of the model's ID field
                (typically ObjectId for MongoDB)

        Returns:
            Optional[T]: The found model instance or None if not found
        """
        return await self.find_one_by({"id": _id})

    async def find_one_by(self, query: dict) -> Optional[T]:
        """Asynchronously find a single model instance by a MongoDB query.

        Args:
            query: MongoDB query dictionary

        Returns:
            Optional[T]: The found model instance or None if not found

        Example:
            user = await repo.find_one_by({"email": "user@example.com"})
        """
        result = await self.get_collection().find_one(self._map_id(query))
        return self.to_model(result) if result else None

    async def find_by_with_output_type(
        self,
        output_type: Type[OutputT],
        query: dict,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[Sort] = None,
        projection: Optional[Dict[str, int]] = None,
    ) -> Iterable[OutputT]:
        """Asynchronously find multiple model instances with custom output type.

        This method allows querying with a different output model than the repository's
        base model type, useful for projections and transformations.

        Args:
            output_type: The Pydantic model class for the output
            query: MongoDB query dictionary
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: List of (field, direction) tuples for sorting
            projection: MongoDB projection dictionary

        Returns:
            Iterable[OutputT]: Iterator of model instances of the specified output type
        """
        mapped_projection = self._map_id(projection) if projection else None
        mapped_sort = self._map_sort(sort) if sort else None
        cursor = self.get_collection().find(self._map_id(query), mapped_projection)
        if limit:
            cursor.limit(limit)
        if skip:
            cursor.skip(skip)
        if mapped_sort:
            cursor.sort(mapped_sort)

        return [self.to_model_custom(output_type, doc) async for doc in cursor]

    async def find_by(
        self,
        query: dict,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[Sort] = None,
        projection: Optional[Dict[str, int]] = None,
    ) -> Iterable[T]:
        """Asynchronously find multiple model instances by a MongoDB query.

        Args:
            query: MongoDB query dictionary
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: List of (field, direction) tuples for sorting
            projection: MongoDB projection dictionary

        Returns:
            Iterable[T]: Iterator of model instances
        """
        return await self.find_by_with_output_type(
            output_type=self._document_class,
            query=query,
            skip=skip,
            limit=limit,
            sort=sort,
            projection=projection,
        )

    async def paginate_with_output_type(
        self,
        output_type: Type[OutputT],
        query: dict,
        limit: int,
        after: Optional[str] = None,
        before: Optional[str] = None,
        sort: Optional[Sort] = None,
        projection: Optional[Dict[str, int]] = None,
    ) -> Iterable[Edge[OutputT]]:
        """Paginate through model instances with custom output type.

        This method implements cursor-based pagination which is more reliable than
        offset-based pagination for large datasets.

        Args:
            output_type: The Pydantic model class for the output
            query: MongoDB query dictionary
            limit: Maximum number of documents per page
            after: Cursor string for fetching next page
            before: Cursor string for fetching previous page
            sort: List of (field, direction) tuples for sorting
            projection: MongoDB projection dictionary

        Returns:
            Iterable[Edge[OutputT]]: Iterator of Edge objects containing model instances
                                  and pagination cursors
        """
        sort_keys = []

        if not sort:
            sort = [("_id", 1)]

        for sort_expression in sort:
            sort_keys.append(sort_expression[0])

        models = await self.find_by_with_output_type(
            output_type,
            query=self.get_pagination_query(
                query=query, after=after, before=before, sort=sort
            ),
            limit=limit,
            sort=sort,
            projection=projection,
        )

        return map(
            lambda model: Edge[OutputT](
                node=model,
                cursor=encode_pagination_cursor(
                    get_pagination_cursor_payload(model, sort_keys)
                ),
            ),
            models,
        )

    async def paginate(
        self,
        query: dict,
        limit: int,
        after: Optional[str] = None,
        before: Optional[str] = None,
        sort: Optional[Sort] = None,
        projection: Optional[Dict[str, int]] = None,
    ) -> Iterable[Edge[T]]:
        """Asynchronously paginate through model instances using cursor-based pagination.

        This method implements cursor-based pagination which is more reliable than
        offset-based pagination for large datasets.

        Args:
            query: MongoDB query dictionary
            limit: Maximum number of documents per page
            after: Cursor string for fetching next page
            before: Cursor string for fetching previous page
            sort: List of (field, direction) tuples for sorting
            projection: MongoDB projection dictionary

        Returns:
            Iterable[Edge[T]]: Iterator of Edge objects containing model instances
                              and pagination cursors

        Example:
            Get first page::

                edges = await repo.paginate({"status": "active"}, limit=10)

            Get next page using the last cursor::

                next_edges = await repo.paginate(
                    {"status": "active"},
                    limit=10,
                    after=list(edges)[-1].cursor
                )
        """
        return await self.paginate_with_output_type(
            self._document_class,
            query,
            limit,
            after=after,
            before=before,
            sort=sort,
            projection=projection,
        )

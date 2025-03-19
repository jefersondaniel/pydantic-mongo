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
    class Meta:
        collection_name: str

    def __init__(self, database: AsyncDatabase):
        self.__database: AsyncDatabase = database
        super().__init__()

    def get_collection(self) -> AsyncCollection:
        """
        Get pymongo collection
        """
        return self.__database[self._collection_name]

    async def save(self, model: T) -> Union[InsertOneResult, UpdateResult]:
        """
        Save entity to database. It will update the entity if it has id, otherwise it will insert it.
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
        """
        Save multiple entities to database
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
        return await self.get_collection().delete_one(
            {"_id": cast(ModelWithId, model).id}
        )

    async def delete_by_id(self, _id: Any):
        return await self.get_collection().delete_one({"_id": _id})

    async def find_one_by_id(self, _id: Any) -> Optional[T]:
        """
        Find entity by id

        Note: The id should be of the same type as the id field in the document class, ie. ObjectId
        """
        return await self.find_one_by({"id": _id})

    async def find_one_by(self, query: dict) -> Optional[T]:
        """
        Find entity by mongo query
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
        """
        Find entities by mongo query allowing custom output type
        :param output_type:
        :param query:
        :param skip:
        :param limit:
        :param sort:
        :param projection:
        :return:
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
        """ "
        Find entities by mongo query
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
        """
        Paginate entities by mongo query allowing custom output type
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
        """
        Paginate entities by mongo query using cursor based pagination

        Return type is an iterable of Edge objects, which contain the model and the cursor
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

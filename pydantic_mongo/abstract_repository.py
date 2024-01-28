from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    Mapping,
    List,
)

import asyncio

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult, BulkWriteResult, InsertManyResult

from motor import motor_asyncio

from .pagination import (
    Edge,
    decode_pagination_cursor,
    encode_pagination_cursor,
    get_pagination_cursor_payload,
)

import nest_asyncio
nest_asyncio.apply()

T = TypeVar("T", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

Sort = Union[str, Sequence[Tuple[str, int]], Tuple[str, int]]


class AbstractRepository(Generic[T]):
    class Meta:
        collection_name: str

    def __init__(self, database: Database):
        super().__init__()
        self.__database: Database = database
        self.__document_class = (
            getattr(self.Meta, "document_class")
            if hasattr(self.Meta, "document_class")
            else self.__orig_bases__[0].__args__[0]  # type: ignore
        )
        self.__collection_name = self.Meta.collection_name
        self.__validate()

    def get_collection(self) -> Collection:
        """
        Get pymongo collection
        """
        return self.__database[self.__collection_name]

    def __validate(self):
        if not issubclass(self.__document_class, BaseModel):
            raise Exception("Document class should inherit BaseModel")
        if "id" not in self.__document_class.model_fields:
            raise Exception("Document class should have id field")
        if not self.__collection_name:
            raise Exception("Meta should contain collection name")

    @property
    def document_count(self) -> int:
        """
        Get document count
        :return: int
        """
        return self.get_collection().count_documents({})

    @staticmethod
    def to_document(model: T) -> dict:
        """
        Convert model to document
        :param model: Model to convert
        :return: dict
        """
        data = model.model_dump(mode='json')
        data.pop("id")
        if model.id:
            data["_id"] = model.id
        return data

    def __map_id(self, data: dict) -> dict:
        query = data.copy()
        if "id" in data:
            query["_id"] = query.pop("id")
        return query

    def __map_sort(self, sort: Sort) -> str | list[tuple] | list[tuple[str | Any, Any]]:
        result = []
        if isinstance(sort, str):
            if sort == "id":
                sort = "_id"
            return sort
        elif isinstance(sort, tuple):
            if sort[0] == "id":
                sort = ("_id", sort[1])
            return [sort]
        elif isinstance(sort, list):
            for item in sort:
                key = item[0]
                ordering = item[1]
                if key == "id":
                    key = "_id"
                result.append((key, ordering))
        else:
            raise Exception("Sort should be str, tuple or list of tuples")
        return result

    def to_model_custom(self, output_type: Type[OutputT], data: Union[dict, Mapping[str, Any]]) -> OutputT:
        """
        Convert document to model with custom output type
        """
        data_copy = data.copy()
        if "_id" in data_copy:
            data_copy["id"] = data_copy.pop("_id")
        return output_type.model_validate(data_copy)

    def to_model(self, data: Union[dict, Mapping[str, Any]]) -> T:
        """
        Convert document to model
        """
        return self.to_model_custom(self.__document_class, data)

    def save(self, model: T, **kwargs) -> Union[InsertOneResult, UpdateResult]:
        """
        Save entity to database. It will update the entity if it has id, otherwise it will insert it.
        :param model: Model to save
        :param kwargs: kwargs for pymongo insert_one or update_one
        :return: Union[InsertOneResult, UpdateResult]
        """
        document = self.to_document(model)

        if model.id:
            mongo_id = document.pop("_id")
            result = self.get_collection().update_one(
                {"_id": mongo_id}, {"$set": document}, upsert=True, **kwargs
            )
            if result.upserted_id:
                model.id = result.upserted_id
            return result

        result = self.get_collection().insert_one(document, **kwargs)
        model.id = result.inserted_id
        return result

    def save_many(self, models: Iterable[T], **kwargs) -> \
            Union[Tuple[BulkWriteResult, None], Tuple[None, InsertManyResult]]:
        """
        Save multiple entities to database
        :param models: Iterable of models to save
        :param kwargs: kwargs for pymongo insert_many or bulk_write
        :return: Union[Tuple[BulkWriteResult, None], Tuple[None, InsertManyResult]]
        """
        models_to_insert = []
        models_to_update = []

        for model in models:
            if model.id:
                models_to_update.append(model)
            else:
                models_to_insert.append(model)
        result = None
        if len(models_to_insert) > 0:
            result = self.get_collection().insert_many(
                (self.to_document(model) for model in models_to_insert),
                **kwargs
            )

            for idx, inserted_id in enumerate(result.inserted_ids):
                models_to_insert[idx].id = inserted_id

        if len(models_to_update) == 0:
            return None, result

        documents_to_update = [self.to_document(model) for model in models_to_update]
        mongo_ids = [doc.pop("_id") for doc in documents_to_update]
        bulk_operations = [
            UpdateOne({"_id": mongo_id}, {"$set": document}, upsert=True)
            for mongo_id, document in zip(mongo_ids, documents_to_update)
        ]
        bw = self.get_collection().bulk_write(bulk_operations, **kwargs)
        if bw.upserted_ids:
            for idx, inserted_id in enumerate(bw.upserted_ids.values()):
                models_to_update[idx].id = inserted_id
        return bw, result

    def delete_many(self, models: Iterable[T], **kwargs) -> Union[DeleteResult, None]:
        """
        Delete multiple entities from database
        """
        mongo_ids = [model.id for model in models]
        if len(mongo_ids) == 0:
            return None
        return self.get_collection().delete_many({"_id": {"$in": mongo_ids}}, **kwargs)

    def delete(self, model: T, **kwargs) -> DeleteResult:
        return self.get_collection().delete_one({"_id": model.id}, **kwargs)

    def find_one_by_id(self, _id: Union[ObjectId, str], *args, **kwargs) -> Optional[T]:
        """
        Find entity by id

        Note: The id should be of the same type as the id field in the document class, ie. ObjectId
        """
        return self.find_one_by({"id": _id}, *args, **kwargs)

    def find_one_by(self, query: dict, *args, **kwargs) -> Optional[T]:
        """
        Find entity by mongo query
        """
        result = self.get_collection().find_one(self.__map_id(query), *args, **kwargs)
        return self.to_model(result) if result else None

    def find_by_with_output_type(
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
        mapped_projection = self.__map_id(projection) if projection else None
        mapped_sort = self.__map_sort(sort) if sort else None
        cursor = self.get_collection().find(self.__map_id(query), mapped_projection)
        if limit:
            cursor.limit(limit)
        if skip:
            cursor.skip(skip)
        if sort:
            cursor.sort(mapped_sort)
        return map(lambda doc: self.to_model_custom(output_type, doc), cursor)

    def find_by(
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
        return self.find_by_with_output_type(
            output_type=self.__document_class,
            query=query,
            skip=skip,
            limit=limit,
            sort=sort,
            projection=projection,
        )

    def get_pagination_query(
        self,
        query: dict,
        after: Optional[str] = None,
        before: Optional[str] = None,
        sort: Optional[Sort] = None,
    ) -> dict:
        """
        Build pagination query based on the cursor and sort
        """
        generated_query: dict = {"$and": [query]}
        selected_cursor = after or before

        if selected_cursor and sort:
            cursor_data = decode_pagination_cursor(selected_cursor)
            dict_values = []
            for i, sort_expression in enumerate(sort):
                if after:
                    compare_operator = "$gt" if sort_expression[1] > 0 else "$lt"
                else:
                    compare_operator = "$lt" if sort_expression[1] > 0 else "$gt"
                dict_values.append(
                    (sort_expression[0], {compare_operator: cursor_data[i]})
                )
            generated_query["$and"].append(dict(dict_values))

        if len(generated_query["$and"]) == 1:
            generated_query = query or {}

        return generated_query

    def paginate_with_output_type(
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

        models = self.find_by_with_output_type(
            output_type,
            query=self.get_pagination_query(
                query=query, after=after, before=before, sort=sort
            ),
            limit=limit,
            sort=sort,
            projection=projection,
        )

        return map(
            lambda model: Edge[T](
                node=model,
                cursor=encode_pagination_cursor(
                    get_pagination_cursor_payload(model, sort_keys)
                ),
            ),
            models,
        )

    def paginate(
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
        return self.paginate_with_output_type(
            self.__document_class,
            query,
            limit,
            after=after,
            before=before,
            sort=sort,
            projection=projection,
        )

    def paginate_simple(self, query: dict, limit: int = 25, page: int = 1, **kwargs):
        """
        Paginate entities by mongo query using simple pagination
        """
        if page <= 0:
            page = 1
        skip = (page - 1) * limit
        return [x for x in self.find_by(query, skip=skip, limit=limit, **kwargs)]


class AsyncAbstractRepository(Generic[T]):
    class Meta:
        collection_name: str

    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__()
        self.__database: AsyncIOMotorDatabase = database
        self.__document_class = (
            getattr(self.Meta, "document_class")
            if hasattr(self.Meta, "document_class")
            else self.__orig_bases__[0].__args__[0]  # type: ignore
        )
        self.__collection_name = self.Meta.collection_name
        self.__validate()

    @property
    def document_count(self) -> int:
        """
        Get document count
        :return: int
        """

        return self._future(self.get_collection().count_documents({}))

    def __validate(self):
        if not issubclass(self.__document_class, BaseModel):
            raise Exception("Document class should inherit BaseModel")
        if "id" not in self.__document_class.model_fields:
            raise Exception("Document class should have id field")
        if not self.__collection_name:
            raise Exception("Meta should contain collection name")

    @staticmethod
    def to_document(model: T) -> dict:
        """
        Convert model to document
        :param model: Model to convert
        :return: dict
        """
        data = model.model_dump(mode='json')
        data.pop("id")
        if model.id:
            data["_id"] = model.id
        return data

    def __map_id(self, data: dict) -> dict:
        query = data.copy()
        if "id" in data:
            query["_id"] = query.pop("id")
        return query

    def __map_sort(self, sort: Sort) -> str | list[tuple] | list[tuple[str | Any, Any]]:
        result = []
        if isinstance(sort, str):
            if sort == "id":
                sort = "_id"
            return sort
        elif isinstance(sort, tuple):
            if sort[0] == "id":
                sort = ("_id", sort[1])
            return [sort]
        elif isinstance(sort, list):
            for item in sort:
                key = item[0]
                ordering = item[1]
                if key == "id":
                    key = "_id"
                result.append((key, ordering))
        else:
            raise Exception("Sort should be str, tuple or list of tuples")
        return result

    def to_model_custom(self, output_type: Type[OutputT], data: Union[dict, Mapping[str, Any]]) -> OutputT:
        """
        Convert document to model with custom output type
        """
        data_copy = data.copy()
        if "_id" in data_copy:
            data_copy["id"] = data_copy.pop("_id")
        return output_type.model_validate(data_copy)

    def get_collection(self) -> motor_asyncio.AsyncIOMotorCollection:
        """
        Get pymongo collection
        """
        return self.__database[self.__collection_name]

    async def find_one_by_id(self, _id: Union[ObjectId, str], *args, **kwargs) -> Optional[T]:
        """
        Find entity by id

        Note: The id should be of the same type as the id field in the document class, ie. ObjectId
        """
        return await self.find_one_by({"id": _id}, *args, **kwargs)

    async def find_one_by(self, query: dict, *args, **kwargs) -> Optional[T]:
        """
        Find entity by mongo query
        """
        result = await self.get_collection().find_one(self.__map_id(query), *args, **kwargs)
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
        mapped_projection = self.__map_id(projection) if projection else None
        mapped_sort = self.__map_sort(sort) if sort else None
        cursor = self.get_collection().find(self.__map_id(query), mapped_projection)
        if limit:
            cursor.limit(limit)
        if skip:
            cursor.skip(skip)
        if sort:
            cursor.sort(mapped_sort)
        return map(lambda doc: self.to_model_custom(output_type, doc), await cursor.to_list(limit))

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
            output_type=self.__document_class,
            query=query,
            skip=skip,
            limit=limit,
            sort=sort,
            projection=projection,
        )

    async def paginate_simple(self, query: dict, limit: int = 25, page: int = 1, **kwargs):
        """
        Paginate entities by mongo query using simple pagination
        :param query:
        :param limit:
        :param page:
        :param kwargs:
        :return:
        """
        if page <= 0:
            page = 1
        skip = (page - 1) * limit
        return [x for x in await self.find_by(query, skip=skip, limit=limit, **kwargs)]

    async def save(self, model: T, **kwargs) -> Union[InsertOneResult, UpdateResult]:
        """
        Save entity to database. It will update the entity if it has id, otherwise it will insert it.
        :param model: Model to save
        :param kwargs: kwargs for pymongo insert_one or update_one
        :return: Union[InsertOneResult, UpdateResult]
        """
        document = self.to_document(model)

        if model.id:
            mongo_id = document.pop("_id")
            result = await self.get_collection().update_one(
                {"_id": mongo_id}, {"$set": document}, upsert=True, **kwargs
            )
            if result.upserted_id:
                model.id = result.upserted_id
            return result

        result = await self.get_collection().insert_one(document, **kwargs)
        model.id = result.inserted_id
        return result

    async def save_many(self, models: Iterable[T], **kwargs) -> \
            Union[Tuple[BulkWriteResult, None], Tuple[None, InsertManyResult]]:
        """
        Save multiple entities to database
        :param models: Iterable of models to save
        :param kwargs: kwargs for pymongo insert_many or bulk_write
        :return: Union[Tuple[BulkWriteResult, None], Tuple[None, InsertManyResult]]
        """
        models_to_insert = []
        models_to_update = []

        for model in models:
            if model.id:
                models_to_update.append(model)
            else:
                models_to_insert.append(model)
        result = None
        if len(models_to_insert) > 0:
            result = await self.get_collection().insert_many(
                (self.to_document(model) for model in models_to_insert),
                **kwargs
            )

            for idx, inserted_id in enumerate(result.inserted_ids):
                models_to_insert[idx].id = inserted_id

        if len(models_to_update) == 0:
            return None, result

        documents_to_update = [self.to_document(model) for model in models_to_update]
        mongo_ids = [doc.pop("_id") for doc in documents_to_update]
        bulk_operations = [
            UpdateOne({"_id": mongo_id}, {"$set": document}, upsert=True)
            for mongo_id, document in zip(mongo_ids, documents_to_update)
        ]
        bw = await self.get_collection().bulk_write(bulk_operations, **kwargs)
        if bw.upserted_ids:
            for idx, inserted_id in enumerate(bw.upserted_ids.values()):
                models_to_update[idx].id = inserted_id
        return bw, result

    async def delete_many(self, models: Iterable[T], **kwargs) -> Union[DeleteResult, None]:
        """
        Delete multiple entities from database
        """
        mongo_ids = [model.id for model in models]
        if len(mongo_ids) == 0:
            return None
        return await self.get_collection().delete_many({"_id": {"$in": mongo_ids}}, **kwargs)

    async def delete(self, model: T, **kwargs) -> DeleteResult:
        """
        Delete entity from database
        :param model:
        :param kwargs:
        :return:
        """
        return await self.get_collection().delete_one({"_id": model.id}, **kwargs)

    def _future(self, coro):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(coro)
        loop.run_until_complete(future)
        r = future.result()
        return r

    def to_model(self, data: Union[dict, Mapping[str, Any]]) -> T:
        """
        Convert document to model
        """
        return self.to_model_custom(self.__document_class, data)

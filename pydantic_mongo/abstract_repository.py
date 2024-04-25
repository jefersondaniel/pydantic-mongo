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
    cast,
)

from pydantic import BaseModel
from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import InsertOneResult, UpdateResult

from .pagination import (
    Edge,
    decode_pagination_cursor,
    encode_pagination_cursor,
    get_pagination_cursor_payload,
)

T = TypeVar("T", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)
Sort = Sequence[Tuple[str, int]]


class ModelWithId(BaseModel):
    id: Any


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

    """
    Get pymongo collection
    """

    def get_collection(self) -> Collection:
        return self.__database[self.__collection_name]

    def __validate(self):
        if "id" not in self.__document_class.model_fields:
            raise Exception("Document class should have id field")
        if not self.__collection_name:
            raise Exception("Meta should contain collection name")

    @staticmethod
    def to_document(model: T) -> dict:
        """
        Convert model to document
        :param model:
        :return: dict
        """
        model_with_id = cast(ModelWithId, model)
        data = model_with_id.model_dump()
        data.pop("id")
        if model_with_id.id:
            data["_id"] = model_with_id.id
        return data

    def __map_id(self, data: dict) -> dict:
        query = data.copy()
        if "id" in data:
            query["_id"] = query.pop("id")
        return query

    def __map_sort(self, sort: Sort) -> Optional[Sort]:
        result = []
        for item in sort:
            key = item[0]
            ordering = item[1]
            if key == "id":
                key = "_id"
            result.append((key, ordering))
        return result

    def to_model_custom(self, output_type: Type[OutputT], data: dict) -> OutputT:
        """
        Convert document to model with custom output type
        """
        data_copy = data.copy()
        if "_id" in data_copy:
            data_copy["id"] = data_copy.pop("_id")
        return output_type.model_validate(data_copy)

    def to_model(self, data: dict) -> T:
        """
        Convert document to model
        """
        return self.to_model_custom(self.__document_class, data)

    def save(self, model: T) -> Union[InsertOneResult, UpdateResult]:
        """
        Save entity to database. It will update the entity if it has id, otherwise it will insert it.
        """
        document = self.to_document(model)
        model_with_id = cast(ModelWithId, model)

        if model_with_id.id:
            mongo_id = document.pop("_id")
            return self.get_collection().update_one(
                {"_id": mongo_id}, {"$set": document}, upsert=True
            )

        result = self.get_collection().insert_one(document)
        model_with_id.id = result.inserted_id
        return result

    def save_many(self, models: Iterable[T]):
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
            result = self.get_collection().insert_many(
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
        self.get_collection().bulk_write(bulk_operations)

    def delete(self, model: T):
        return self.get_collection().delete_one({"_id": cast(ModelWithId, model).id})

    def delete_by_id(self, _id: Any):
        return self.get_collection().delete_one({"_id": _id})

    def find_one_by_id(self, _id: Any) -> Optional[T]:
        """
        Find entity by id

        Note: The id should be of the same type as the id field in the document class, ie. ObjectId
        """
        return self.find_one_by({"id": _id})

    def find_one_by(self, query: dict) -> Optional[T]:
        """
        Find entity by mongo query
        """
        result = self.get_collection().find_one(self.__map_id(query))
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
        if mapped_sort:
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
            lambda model: Edge[OutputT](
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

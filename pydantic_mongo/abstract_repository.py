from typing import Dict, Optional, Iterable, Sequence, Type, Tuple, TypeVar, Generic
from pydantic import BaseModel
from .pagination import Edge, encode_pagination_cursor, decode_pagination_cursor, get_pagination_cursor_payload

T = TypeVar('T', bound=BaseModel)
OutputT = TypeVar('OutputT', bound=BaseModel)

Sort = Sequence[Tuple[str, int]]


class AbstractRepository(Generic[T]):
    def __init__(self, database):
        super().__init__()
        self.__database = database
        self.__document_class = self.__orig_bases__[0].__args__[0]
        self.__collection_name = self.Meta.collection_name
        self.__validate()

    def get_collection(self):
        return self.__database[self.__collection_name]

    def __validate(self):
        if not issubclass(self.__document_class, BaseModel):
            raise Exception('Document class should inherit BaseModel')
        if 'id' not in self.__document_class.__fields__:
            raise Exception('Document class should have id field')
        if not self.__collection_name:
            raise Exception('Meta should contain collection name')

    def to_document(self, model: T) -> dict:
        result = model.dict()
        result.pop('id')
        if model.id:
            result['_id'] = model.id
        return result

    def __map_id(self, data: dict) -> dict:
        query = data.copy()
        if 'id' in data:
            query['_id'] = query.pop('id')
        return query

    def __map_sort(self, sort: Sort) -> Optional[Sort]:
        result = []
        for item in sort:
            key = item[0]
            ordering = item[1]
            if key == 'id':
                key = '_id'
            result.append((key, ordering))
        return result

    def to_model_custom(self, output_type: Type[OutputT], data: dict) -> OutputT:
        data_copy = data.copy()
        if '_id' in data_copy:
            data_copy['id'] = data_copy.pop('_id')
        return output_type.parse_obj(data_copy)

    def to_model(self, data: dict) -> T:
        return self.to_model_custom(self.__document_class, data)

    def save(self, model: T):
        document = self.to_document(model)

        if model.id:
            mongo_id = document.pop('_id')
            self.get_collection().update_one({'_id': mongo_id}, {'$set': document})
            return

        result = self.get_collection().insert_one(document)
        model.id = result.inserted_id
        return result

    def delete(self, model: T):
        return self.get_collection().delete_one({'_id': model.id})

    def find_one_by_id(self, id: str) -> Optional[T]:
        return self.find_one_by({'id': id})

    def find_one_by(self, query: dict) -> Optional[T]:
        result = self.get_collection().find_one(self.__map_id(query))
        return self.to_model(result) if result else None

    def find_by_with_output_type(
        self,
        output_type: Type[OutputT],
        query: dict,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Sort = None,
        projection: Dict[str, int] = None
    ) -> Iterable[OutputT]:
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
        sort: Sort = None,
        projection: Dict[str, int] = None
    ) -> Iterable[T]:
        return self.find_by_with_output_type(
            output_type=self.__document_class,
            query=query,
            skip=skip,
            limit=limit,
            sort=sort,
            projection=projection
        )

    def get_pagination_query(
        self,
        query: dict,
        after: str = None,
        before: str = None,
        sort: Sort = None
    ) -> dict:
        generated_query: dict = {'$and': [query]}
        selected_cursor = after or before

        if selected_cursor and sort:
            cursor_data = decode_pagination_cursor(selected_cursor)
            dict_values = []
            for i, sort_expression in enumerate(sort):
                if after:
                    compare_operator = '$gt' if sort_expression[1] > 0 else '$lt'
                else:
                    compare_operator = '$lt' if sort_expression[1] > 0 else '$gt'
                dict_values.append((
                    sort_expression[0],
                    {compare_operator: cursor_data[i]}
                ))
            generated_query['$and'].append(dict(dict_values))

        if len(generated_query['$and']) == 1:
            generated_query = query or {}

        return generated_query

    def paginate_with_output_type(
        self,
        output_type: Type[OutputT],
        query: dict,
        limit: int,
        after: str = None,
        before: str = None,
        sort: Sort = None,
        projection: Dict[str, int] = None
    ) -> Iterable[Edge[OutputT]]:
        sort_keys = []

        if not sort:
            sort = [('_id', 1)]

        for sort_expression in sort:
            sort_keys.append(sort_expression[0])

        models = self.find_by_with_output_type(
            output_type,
            query=self.get_pagination_query(
                query=query,
                after=after,
                before=before,
                sort=sort
            ),
            limit=limit,
            sort=sort,
            projection=projection
        )

        return map(
            lambda model: Edge[T](
                node=model,
                cursor=encode_pagination_cursor(get_pagination_cursor_payload(model, sort_keys))
            ),
            models
        )

    def paginate(
        self,
        query: dict,
        limit: int,
        after: str = None,
        before: str = None,
        sort: Sort = None,
        projection: Dict[str, int] = None
    ) -> Iterable[Edge[T]]:
        return self.paginate_with_output_type(
            self.__document_class,
            query,
            limit,
            after=after,
            before=before,
            sort=sort,
            projection=projection
        )

from typing import Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


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

    def __to_query(self, data: dict):
        query = data.copy()
        if 'id' in data:
            query['_id'] = query.pop('id')
        return query

    def to_model(self, data: dict) -> T:
        data_copy = data.copy()
        if '_id' in data_copy:
            data_copy['id'] = data_copy.pop('_id')
        return self.__document_class.parse_obj(data_copy)

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
        result = self.get_collection().find_one(self.__to_query(query))
        return self.to_model(result) if result else None

    def find_by(
        self,
        query: dict,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort=None
    ):
        cursor = self.get_collection().find(self.__to_query(query))
        if limit:
            cursor.limit(limit)
        if skip:
            cursor.skip(skip)
        if sort:
            cursor.sort(sort)
        return map(self.to_model, cursor)

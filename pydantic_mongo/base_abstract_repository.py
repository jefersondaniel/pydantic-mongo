from typing import Any, Generic, Optional, Sequence, Tuple, Type, TypeVar, cast

from pydantic import BaseModel

from .pagination import decode_pagination_cursor

T = TypeVar("T", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)
Sort = Sequence[Tuple[str, int]]


class ModelWithId(BaseModel):
    id: Any


class BaseAbstractRepository(Generic[T]):
    class Meta:
        collection_name: str

    def __init__(self):
        super().__init__()

        self._document_class = (
            getattr(self.Meta, "document_class")
            if hasattr(self.Meta, "document_class")
            else self.__orig_bases__[0].__args__[0]  # type: ignore
        )
        self._collection_name = self.Meta.collection_name
        self.__validate()

    def __validate(self):
        if (
            "id" not in self._document_class.model_fields
            and "id" not in self._document_class.model_computed_fields
        ):
            raise Exception("Document class should have id field")
        if not self._collection_name:
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

    def _map_id(self, data: dict) -> dict:
        query = data.copy()
        if "id" in data:
            query["_id"] = query.pop("id")
        return query

    def _map_sort(self, sort: Sort) -> Optional[Sort]:
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
        Convert a MongoDB document to a Pydantic model with a custom output type.

        This method handles the mapping of MongoDB's ``_id`` field to the Pydantic model's ``id`` field,
        ensuring seamless integration between raw MongoDB data and Pydantic models.
        It's particularly useful when working with custom projections or aggregations where
        the output structure differs from the repository's primary model.

        Args:
            output_type: The Pydantic model class to convert the data to.
            data: The raw dictionary data from MongoDB.

        Returns:
            OutputT: An instance of the specified Pydantic model with the data mapped accordingly.
        """
        data_copy = data.copy()
        if "_id" in data_copy:
            data_copy["id"] = data_copy.pop("_id")
        return output_type.model_validate(data_copy)

    def to_model(self, data: dict) -> T:
        """
        Convert a MongoDB document to the repository's primary Pydantic model.

        This method is a convenience wrapper around ``to_model_custom`` that uses the
        repository's default model type. It also handles the mapping of MongoDB's ``_id``
        field to the Pydantic model's ``id`` field.

        Args:
            data: The raw dictionary data from MongoDB.

        Returns:
            T: An instance of the repository's primary Pydantic model with the data mapped accordingly.
        """
        return self.to_model_custom(self._document_class, data)

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

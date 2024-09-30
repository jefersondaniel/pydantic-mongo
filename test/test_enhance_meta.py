import pytest
from pydantic import BaseModel
from typing_extensions import Optional

from pydantic_mongo import AbstractRepository, PydanticObjectId


class HamModel(BaseModel):
    id: Optional[PydanticObjectId]
    name: str


class HamRepository(AbstractRepository):
    class Meta:
        collection_name = "ham"
        document_class = HamModel


@pytest.fixture(scope="session")
def ham_repo(database):
    return HamRepository(database=database)


@pytest.fixture
def clean_ham_collection(ham_repo):
    return ham_repo.get_collection().delete_many({})


def test_repository_with_v2_meta(ham_repo):
    assert not list(ham_repo.find_by({})), "should have no documents in db"
    assert ham_repo.get_collection().name == "ham"


def test_save_with_new_repo(clean_ham_collection, ham_repo):
    m = HamModel(id=None, name="wilfred")
    assert m.id is None, "should have no id"
    ham_repo.save(m)
    assert m.id

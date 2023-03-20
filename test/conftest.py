import mongomock
import pytest
from pymongo.database import Database


@pytest.fixture(scope="session")
def database():
    return mongomock.MongoClient().db

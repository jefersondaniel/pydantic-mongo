import mongomock
import pytest


@pytest.fixture(scope="session")
def database():
    return mongomock.MongoClient().db

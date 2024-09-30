import xml.etree.ElementTree as ET
from os import system
from os.path import dirname, join

from phulpy import task


@task
def test(phulpy):
    phulpy.start(["lint", "typecheck", "unit_test"])


@task
def lint(phulpy):
    pydantic_mongo_dir = "pydantic_mongo"
    for cmd, message in (
        (f"flake8 {pydantic_mongo_dir}", "please check flake8 errors"),
        (f"isort {pydantic_mongo_dir} --profile black --check", "please run isort!"),
        (f"black {pydantic_mongo_dir} --check", "please run black!"),
    ):
        result = system(cmd)
        if result:
            raise Exception(f"Lint failed: {message}")


@task
def unit_test(phulpy):
    result = system(
        "pytest --cov-report term-missing"
        + " --cov-report xml --cov=pydantic_mongo test"
    )
    if result:
        raise Exception("Unit tests failed")
    coverage_path = join(dirname(__file__), "coverage.xml")
    xml = ET.parse(coverage_path).getroot()
    if float(xml.get("line-rate")) < 1:
        raise Exception("Unit test is not fully covered")


@task
def integration_test(phulpy):
    result = system("pytest integration_test")
    if result:
        raise Exception("Integration tests failed")


@task
def typecheck(phulpy):
    result = system("mypy pydantic_mongo test --check-untyped-defs")
    if result:
        raise Exception("lint test failed")

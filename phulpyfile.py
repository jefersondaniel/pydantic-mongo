import xml.etree.ElementTree as ET
from os import system, unlink
from os.path import dirname, join
from phulpy import task


@task
def test(phulpy):
    phulpy.start(['lint', 'typecheck', 'unit_test'])


@task
def lint(phulpy):
    result = system('flake8 pydantic_mongo')
    if result:
        raise Exception('lint test failed')


@task
def unit_test(phulpy):
    result = system(
        'pytest --cov-report term-missing'
        + ' --cov-report xml --cov=pydantic_mongo test'
    )
    if result:
        raise Exception('Unit tests failed')
    coverage_path = join(dirname(__file__), 'coverage.xml')
    xml = ET.parse(coverage_path).getroot()
    unlink(coverage_path)
    if float(xml.get('line-rate')) < 1:
        raise Exception('Unit test is not fully covered')


@task
def typecheck(phulpy):
    result = system(r'find ./pydantic_mongo -name "*.py" -exec mypy --ignore-missing-imports --follow-imports=skip --strict-optional {} \+')
    if result:
        raise Exception('lint test failed')

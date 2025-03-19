import os

from setuptools import setup

long_description = open("README.md", "r").read()

package_root = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(package_root, "pydantic_mongo/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

setup(
    name="pydantic-mongo",
    version=version,
    packages=["pydantic_mongo"],
    setup_requires=["wheel"],
    install_requires=["pymongo>=4.9,<5.0", "pydantic>=2.0.2,<3.0.0"],
    description="Document object mapper for pydantic and pymongo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jefersondaniel/pydantic-mongo",
    author="Jeferson Daniel",
    author_email="jeferson.daniel412@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)

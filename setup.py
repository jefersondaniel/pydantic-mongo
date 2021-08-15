from setuptools import setup

long_description = open('README.rst', 'r').read()

setup(
    name='pydantic-mongo',
    version='0.0.1',
    packages=['pydantic_mongo'],
    setup_requires=['wheel'],
    install_requires=[
        'pymongo>=3.12,<4.0',
        'pydantic>=1.6.2,<2.0.0'
    ],
    entry_points={
        "console_scripts": [
            "pydantic_mongo = pydantic_mongo.__main__:__main__"
        ],
    },
    description="Document object mapper for pydantic and pymongo",
    long_description=long_description,
    url='https://github.com/jefersondaniel/pydantic-mongo',
    author='Jeferson Daniel',
    author_email='jeferson.daniel412@gmail.com',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    python_requires=">=3.6"
)

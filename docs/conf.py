import os
import sys


sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../pydantic_mongo'))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pydantic-mongo'
copyright = '2025, Jeferson Daniel'
author = 'Jeferson Daniel'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pymongo': ('https://pymongo.readthedocs.io/en/stable/', None),
    'pydantic': ('https://docs.pydantic.dev/', None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = 'Pydantic Mongo'

# GitHub edit link
html_context = {
    'display_github': True,
    'github_user': 'jefersondaniel',
    'github_repo': 'pydantic-mongo',
    'github_version': 'main',
    'conf_py_path': '/docs/',
}

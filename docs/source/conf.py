import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = 'SQLPyHelper'
copyright = '2026, Adebayo Olaonipekun'
author = 'Adebayo Olaonipekun'
release = '0.1.5'

extensions = [
    "sphinx.ext.autodoc",  # generates API docs from docstrings
    "sphinx.ext.viewcode",  # adds links to source code
    "sphinx.ext.napoleon",  # supports Google/NumPy style docstrings
    "myst_parser",  # write docs in Markdown instead of RST
]

templates_path = ['_templates']
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_theme_options = {
    "navigation_depth": 4,
    "titles_only": False,
}

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

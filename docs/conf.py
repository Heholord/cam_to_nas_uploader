# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'cam_scripts'
copyright = '2026, Manuel Esberger'
author = 'Manuel Esberger'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


import os
import sys

# Add your script directory to path
sys.path.insert(0, os.path.abspath('../'))

extensions = [
    'sphinx.ext.autodoc',      # Auto-generate from docstrings
    'sphinx.ext.napoleon',     # Support Google/NumPy style docstrings
    'sphinx.ext.viewcode',     # Link to source code
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

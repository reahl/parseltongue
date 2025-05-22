# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import datetime

# Add the project directory to the path so sphinx can find the modules
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'parseltongue'
copyright = f'2022-{datetime.now().year}, Reahl Software Services (Pty) Ltd'
author = 'Reahl Software Services (Pty) Ltd'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.apidoc',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------
# autodoc settings
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'exclude-members': '__dict__,__weakref__,__module__'
}


# Skip members without docstrings
def skip_without_docstring(app, what, name, obj, skip, options):
    # Skip if there's no docstring
    if not obj.__doc__:
        return True
    # Skip special members except for __init__
    if name.startswith('__') and name != '__init__':
        return True
    # Use the default skip logic for everything else
    return skip

def setup(app):
    app.connect('autodoc-skip-member', skip_without_docstring)

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# apidoc settings
apidoc_module_dir = '../ptongue'
apidoc_output_dir = 'api'
apidoc_excluded_paths = ['../ptongue/gemproxy*', '../ptongue/gemstone.py']
apidoc_separate_modules = True
apidoc_toc_file = 'modules'
apidoc_module_first = True

# Additional apidoc options to exclude undocumented modules
apidoc_extra_args = ['--no-headings', '--no-toc', '--force']
#apidoc_extra_args = [ '--no-toc', '--force']

# Intersphinx settings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

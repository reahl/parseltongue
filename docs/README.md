# Parseltongue Documentation

This directory contains the documentation for the Parseltongue project, built with Sphinx.

## Building the Documentation

To build the documentation:

```bash
# Install the documentation dependencies
pip install -e ".[docs]"

# Build the HTML documentation
cd docs
make html
```

The built documentation will be available in the `_build/html` directory.

## Documentation Structure

- `conf.py`: Sphinx configuration file
- `index.rst`: Documentation homepage
- `*.md`: Markdown documentation files
- `api/`: Auto-generated API documentation (created during build)
- `_build/`: Built documentation (created during build)
- `_static/`: Static files (CSS, JavaScript, images)
- `_templates/`: Custom templates

## Adding Documentation

To add new documentation:

1. Create a new Markdown (`.md`) or reStructuredText (`.rst`) file
2. Add it to the appropriate toctree in `index.rst` or another document

## Generating API Documentation

API documentation is automatically generated during the build process using `sphinxcontrib-apidoc`. 
The configuration in `conf.py` controls which modules are documented.

## Extensions Used

- `sphinx.ext.autodoc`: Automatically generate API documentation
- `sphinx.ext.viewcode`: Add links to source code
- `sphinx.ext.napoleon`: Support for Google-style and NumPy-style docstrings
- `sphinx.ext.intersphinx`: Link to other projects' documentation
- `sphinxcontrib.apidoc`: Run sphinx-apidoc automatically during build
- `myst_parser`: Support for Markdown files

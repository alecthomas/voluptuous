# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'voluptuous'
copyright = '2023, Alec Thomas'
author = 'Alec Thomas'
release = __import__('voluptuous').__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx.ext.githubpages']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_theme_options = {
    "description": "Python data validation library",
    "github_user": "alecthomas",
    "github_repo": "voluptuous",
    "github_button": True,
    "extra_nav_links": {
        "Repository": "https://github.com/alecthomas/voluptuous",
        "Current Release": "https://github.com/alecthomas/voluptuous/releases/latest",
    }
}

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document) are in another directory,
# add these directories to sys.path here.
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Pili - Exercise Tracker Chatbot'
copyright = '2025, Pili Development Team'
author = 'Pili Development Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
    'sphinx_autodoc_typehints',
    'sphinx_copybutton',
    'autoapi.extension',
]

# AutoAPI configuration
autoapi_dirs = ['../agents', '../core', '../models', '../services', '../tools', '../config']
autoapi_type = 'python'
autoapi_file_patterns = ['*.py']
autoapi_generate_api_docs = True
autoapi_add_toctree_entry = False
autoapi_member_order = 'groupwise'
autoapi_python_class_content = 'both'
autoapi_keep_files = False
autoapi_options = [
    'members',
    'undoc-members',
    'show-inheritance',
    'show-module-summary',
    'special-members',
    'imported-members'
]
autoapi_ignore = [
    '*migrations*',
    '*tests*',
    '*test_*',
]

# MyST Parser configuration
source_suffix = {
    '.rst': None,
    '.md': None,
}

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_typehints = 'description'
autodoc_member_order = 'bysource'

# Templates path
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = [
    '_build', 
    'Thumbs.db', 
    '.DS_Store',
    'README.md',  # Exclude problematic markdown files
    'SETUP_COMPLETE.md',
    'AUTOMATION_COMPLETE.md',
    'BUILD_FIXES_APPLIED.md',
    'AUTOAPI_WARNING_FIXES.md',
    # Exclude individual AutoAPI module index files to prevent toctree warnings
    'autoapi/Scaffold-your-shape-Chatbot/agents/index.rst',
    'autoapi/Scaffold-your-shape-Chatbot/config/index.rst',
    'autoapi/Scaffold-your-shape-Chatbot/core/index.rst',
    'autoapi/Scaffold-your-shape-Chatbot/models/index.rst',
    'autoapi/Scaffold-your-shape-Chatbot/services/index.rst',
    'autoapi/Scaffold-your-shape-Chatbot/tools/index.rst',
]

# Master document
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Theme options
html_theme_options = {
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980b9',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom CSS
html_css_files = [
    'custom.css',
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'fncychap': '',
    'maketitle': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'Pili.tex', 'Pili - Exercise Tracker Chatbot Documentation',
     'Pili Development Team', 'manual'),
]

# -- Options for manual page output ------------------------------------------
# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'pili', 'Pili - Exercise Tracker Chatbot Documentation',
     [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------
# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'Pili', 'Pili - Exercise Tracker Chatbot Documentation',
     author, 'Pili', 'A sophisticated multiagent chatbot for exercise tracking.',
     'Miscellaneous'),
]

# -- Extension configuration -------------------------------------------------

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'fastapi': ('https://fastapi.tiangolo.com', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
}

# Copy button configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# Suppress specific warnings
suppress_warnings = [
    'toc.not_readable',      # Suppress warnings about documents not in toctree
    'ref.doc',               # Suppress warnings about unknown documents
    'toc.not_included',      # Suppress warnings about AutoAPI documents not in toctree
    'autoapi',               # Suppress all AutoAPI warnings
    'autoapi.not_readable',  # Suppress AutoAPI specific warnings
]

# Custom warning suppression function
def setup(app):
    """Custom Sphinx setup function to suppress AutoAPI warnings."""
    # Suppress toctree warnings for autoapi generated files
    def suppress_autoapi_warnings(warning):
        if 'autoapi' in str(warning) and 'toctree' in str(warning):
            return True
        if 'document isn\'t included in any toctree' in str(warning) and 'autoapi' in str(warning):
            return True
        return False
    
    # This doesn't work directly, but we handle it through suppress_warnings above

# Autodoc configuration to handle duplicates
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'no-index': False
} 
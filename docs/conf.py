# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import pkg_resources
sys.path.insert(0, os.path.abspath('../'))


# -- Project information -----------------------------------------------------

project = 'onice_conversion'
copyright = '2021, onice, sneakers-the-rat'
author = 'onice, sneakers-the-rat'

# The full version, including alpha/beta/rc tags
# release = '0.1.0'
release = pkg_resources.get_distribution('onice_conversion').version

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'nbsphinx',
    'nbsphinx_link',
    'autodocsumm'
]

# --------------------------------------------------
# Napoleon config
# --------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_use_param = False
napoleon_use_ivar = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True

# --------------------------------------------------
# Autosummary & Autodoc config
# --------------------------------------------------

autoclass_content = "both"
autodoc_member_order = "bysource"
autodata_content = "both"
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'private-members': False,
    'show-inheritance': False,
    'toctree': True,
    'undoc-members': True,
    'autosummary': True
}

# --------------------------------------------------
# nbsphinx config
# --------------------------------------------------

nbsphinx_kernel_name = 'python3'

# robbed from https://github.com/spatialaudio/nbsphinx/blob/feb64b00a0c0310991f0c17c712842725c43d163/doc/conf.py#L34
# see https://nbsphinx.readthedocs.io/en/0.8.3/prolog-and-epilog.html
nbsphinx_prolog = r"""
{% set docname = env.doc2path(env.docname, base=None).replace('nblink', 'ipynb') %}
.. raw:: html

    <div class="admonition note">
      This page was generated from
      <a class="reference external" href="https://github.com/o-nice/onice-conversion/blob/main/{{ docname|e }}">{{ docname|e }}</a>.
      Interactive online version:
      <span style="white-space: nowrap;"><a href="https://mybinder.org/v2/gh/o-nice/onice-conversion/main?filepath={{ docname|e }}"><img alt="Binder badge" src="https://mybinder.org/badge_logo.svg" style="vertical-align:text-bottom"></a>.</span>
    </div>
    
.. raw:: latex

    \nbsphinxstartnotebook{\scriptsize\noindent\strut
    \textcolor{gray}{The following section was generated from
    \sphinxcode{\sphinxupquote{\strut {{ docname | escape_latex }}}} \dotfill}}
"""

# --------------------------------------------------
# intersphinx
# --------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'nwb-conversion-tools': ('https://nwb-conversion-tools.readthedocs.io/en/master/', None),
    'pynwb': ('https://pynwb.readthedocs.io/en/stable/', None)
}

# --------------------------------------------------

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
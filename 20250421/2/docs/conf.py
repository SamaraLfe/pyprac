import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Игра MOOD'
copyright = '2025, Dmitry'
author = 'Dmitry'
release = '1.0'

language = 'ru'

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_static_path = ['_static']
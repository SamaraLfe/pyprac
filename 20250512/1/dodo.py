from doit.task import clean_targets
import shutil
import os

DOIT_CONFIG = {'default_tasks': ['html']}

def task_extract():
    """Extract translations"""
    return {
        'actions': ['pybabel extract -o mood/server/locale/messages.pot --input-dirs mood/'],
        'targets': ['mood/server/locale/messages.pot'],
        'clean': [clean_targets],
    }

def task_update():
    """Update translations"""
    return {
        'actions': ['pybabel update -D messages -d mood/server/locale -i mood/server/locale/messages.pot'],
        'file_dep': ['mood/server/locale/messages.pot'],
        'targets': ['mood/server/locale/ru_RU/LC_MESSAGES/messages.po'],
        'clean': [clean_targets],
    }

def task_compile():
    """Compile translations"""
    return {
        'actions': ['pybabel compile -D messages -d mood/server/locale'],
        'file_dep': ['mood/server/locale/ru_RU/LC_MESSAGES/messages.po'],
        'targets': ['mood/server/locale/ru_RU/LC_MESSAGES/messages.mo'],
        'clean': [clean_targets],
    }

def task_i18n():
    """Generate translations"""
    return {
        'actions': [],
        'task_dep': ['extract', 'update', 'compile'],
    }

def task_html():
    """Build HTML documentation"""
    return {
        'actions': ['sphinx-build docs docs/_build'],
        'task_dep': ['compile'],
        'targets': ['docs/_build'],
        'clean': [clean_targets, lambda: shutil.rmtree('docs/_build', ignore_errors=True)],
    }

def task_test():
    """Run pytest-based tests for server and client"""
    return {
        'actions': [
            'pipenv run pytest test_server_commands.py -v',
            'pipenv run pytest test_client_commands.py -v'
        ],
        'file_dep': [
            'test_server_commands.py',
            'test_client_commands.py',
            'mood/server/server.py',
            'mood/client/client.py',
            'mood/common/models.py'
        ],
        'task_dep': ['compile'],
        'clean': [clean_targets],
    }

def task_wheel():
    """Build a Wheel distribution for client and server"""
    return {
        'actions': ['python -m build --wheel'],
        'file_dep': [
            'pyproject.toml',
            'mood/client/client.py',
            'mood/client/__init__.py',
            'mood/client/__main__.py',
            'mood/server/server.py',
            'mood/server/__init__.py',
            'mood/server/__main__.py',
            'mood/common/models.py',
            'mood/common/__init__.py',
            'mood/server/locale/ru_RU/LC_MESSAGES/messages.mo'
        ],
        'targets': ['dist/*.whl'],
        'clean': [clean_targets, lambda: shutil.rmtree('dist', ignore_errors=True), lambda: shutil.rmtree('build', ignore_errors=True)],
    }
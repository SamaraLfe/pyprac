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
        'actions': [],  # Пустой список действий
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
    """Run client+server tests"""
    return {
        'actions': ['python -m unittest discover tests -v'],
        'file_dep': ['tests/test_add_monster.py', 'tests/test_attack_monster.py',
                     'tests/test_move_to_monster.py', 'tests/test_utils.py'],
        'task_dep': ['compile'],
        'clean': [clean_targets, lambda: [os.remove(f) for f in ['test.mood', 'test2.mood'] if os.path.exists(f)]],
    }
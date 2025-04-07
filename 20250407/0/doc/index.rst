Welcome to My Sphinx Documentation
=================================

This documentation demonstrates how to use Sphinx with reStructuredText to document a Python project, including a calendar generator and a command-line interpreter.

To generate a calendar table in reST format for a specific month (where the 1st is a Monday), run:

.. code-block:: bash

   python3 -m restcalend 2024 4

This generates a file (e.g., ``calendar_2024_4.rst``) with a reST table for April 2024. See the :doc:`restcalend` page for details.

The project also includes a command-line interpreter. See the :doc:`cmdscript` page for details.

Contents
--------

.. toctree::
   :maxdepth: 2

   restcalend
   cmdscript
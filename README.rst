.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. +--------------------------------------------------------------------------+
   |                                                                          |
   | Licensed under the Apache License, Version 2.0 (the "License");          |
   | you may not use this file except in compliance with the License.         |
   | You may obtain a copy of the License at                                  |
   |                                                                          |
   |     http://www.apache.org/licenses/LICENSE-2.0                           |
   |                                                                          |
   | Unless required by applicable law or agreed to in writing, software      |
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+

*******************************************************************************
                                    devshim
*******************************************************************************

Overview
===============================================================================

Non-intrusive, portable development support shim. Provides single point of
entry to many common development tasks, everything from running multiple
linters to running tests across multiple Python implementations and versions to
building and publishing packages to PyPI.

*Beware: Alpha software!* This is currently used by some of my own projects,
including `python-lockup <https://github.com/emcd/python-lockup>`_, but is not
considered stable and production-ready yet. In particular, there is some work
to make this fully portable on Windows.

Quick Tour
===============================================================================

::

    $ eval "$(/usr/bin/python3 develop.py ease)"

::

    $ devshim --list
    Subcommands:

      bootstrap                 Bootstraps the development environment and utilities.
      branch-release            Makes a new branch for development torwards a release.
      build-python-venv         Creates virtual environment for requested Python version.
      bump                      Bumps a piece of the current version.
      bump-patch                Bumps to next patch level.
      bump-stage                Bumps to next release stage.
      check-code-style          Checks code style of new changes.
      check-pip-install         Checks import of current package after installation via Pip.
      check-pypi-integrity      Checks integrity of project packages on PyPI.
      check-readme              Checks that the README will render correctly on PyPI.
      check-security-issues     Checks for security issues in utilized packages and tools.
      check-urls                Checks the HTTP URLs in the documentation for liveness.
      clean                     Cleans all caches.
      clean-pycaches            Removes all caches of compiled CPython bytecode.
      clean-python-packages     Removes unused Python packages.
      clean-tool-caches         Clears the caches used by code generation and testing utilities.
      ease                      Prints shell functions for easy invocation of development shim.
      freshen                   Performs the various freshening tasks, cleaning first.
      freshen-asdf              Asks Asdf to update itself.
      freshen-git-hooks         Updates Git hooks to latest tagged release.
      freshen-git-modules       Performs recursive update of all Git modules.
      freshen-python            Updates supported Python minor version to latest patch.
      freshen-python-packages   Updates declared Python packages.
      install-git-hooks         Installs hooks to check goodness of code changes before commit.
      install-python            Installs requested Python version.
      lint                      Lints the source code.
      lint-bandit               Security checks the source code with Bandit.
      lint-mypy                 Lints the source code with Mypy.
      lint-pylint               Lints the source code with Pylint.
      lint-semgrep              Lints the source code with Semgrep.
      make                      Generates all of the artifacts.
      make-html                 Generates documentation as HTML artifacts.
      make-sdist                Packages the Python sources for release.
      make-wheel                Packages a Python wheel for release.
      push                      Pushes commits on current branch, plus all tags.
      release-new-patch         Unleashes a new patch upon the world.
      release-new-stage         Unleashes a new stage upon the world.
      report-coverage           Combines multiple code coverage results into a single report.
      run                       Runs command in virtual environment.
      test                      Runs the test suite.
      upload-github-pages       Publishes Sphinx HTML output to Github Pages for project.
      upload-pypi               Publishes current sdist and wheels to PyPI.
      upload-test-pypi          Publishes current sdist and wheels to Test PyPI.

`More Flair <https://www.imdb.com/title/tt0151804/characters/nm0431918>`_
===============================================================================
...than the required minimum

.. image:: https://img.shields.io/github/last-commit/emcd/python-lockup
   :alt: GitHub last commit
   :target: https://github.com/emcd/python-lockup

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
   :alt: pre-commit
   :target: https://github.com/pre-commit/pre-commit

.. image:: https://img.shields.io/badge/security-bandit-yellow.svg
   :alt: Security Status
   :target: https://github.com/PyCQA/bandit

.. image:: https://img.shields.io/badge/linting-pylint-yellowgreen
   :alt: Static Analysis Status
   :target: https://github.com/PyCQA/pylint

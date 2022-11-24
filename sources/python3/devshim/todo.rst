Prefer Prebuilt Python Executables
===============================================================================

* Pull from https://github.com/indygreg/python-build-standalone/releases/latest

Windows Development Support
===============================================================================

* Investigate ``conda`` for environment management.
  If viable, then recommend its installation instead of ``asdf`` if the
  development environment is not a virtualized Linux, such as WSL.

* Or, manage Pythons on all platforms via ``develop.py``.

Remove Dependency on System ``pip``
===============================================================================

* Some OS distributions make a separate ``python3-pip`` package (or similar),
  which might not be installed by default, even if Python 3 is.

* System Pip may also be out-of-date. Better to guarantee something recent.

* Can bootstrap local installation with ``urllib`` and ``importlib`` from
  https://bootstrap.pypa.io/pip/.

* Maybe place in :file:`.local/caches/devshim/packages/python3/<hash>`,
  where ``hash`` is calculated from SHA-1 of :py:data:`sys.version` and
  the result of :py:func:`platform.uname`. Override with
  :envvar:`DEVSHIM_PYTHON3_PACKAGES_CACHE`.

Remove Dependency on ``git``
===============================================================================

* Will not have to handle Git variants, like TortoiseGit, or Git bridges to
  other SCM systems.

* Can use `Dulwich <https://www.dulwich.io/apidocs/>`, which does not rely on
  Git executable. Will also be more efficient to eliminate subprocess fork-exec
  actions.

More Linters
===============================================================================

* `Fixit <https://github.com/Instagram/Fixit>`

* `Ruff <https://github.com/charliermarsh/ruff>`

* `Tryceratops <https://github.com/guilatrova/tryceratops>`

Installable Devshim Wrapper Script
===============================================================================

* Detects whether it is in a devshim-enabled directory tree.

* May also be segue to providing devshim as a package.

Remove Dependency on ``bump2version``
===============================================================================

* Can work directly with ``__version__`` for package and set ``version`` in
  :file:`pyproject.toml` to ``dynamic``.

* Will need to modify project version reader to support the ``dynamic`` field.

Remove Dependency on ``invoke``
===============================================================================

* Topological sort of tasks.

* Deduplication of tasks.

* Context managers for task execution.

* Pseudo-TTY support.

* Dynamic passing of arguments to subtasks.

* Surfacing parameters from subtasks.

* Handle via ``develop.py``.

* Possibly use `Typer <https://typer.tiangolo.com/>` as partial replacement.

Provide In-Tree PEP 517 Build Backend
===============================================================================

* Proxy to Setuptools 'build_meta' backend, once it supports the 'build_base'
  and 'egg_base' options. Can use the command options overrides now baked in
  'setup.py'.

* Or proxy to `Enscons <https://pypi.org/project/enscons/>`_.

* Or write our own, borrowing sdist- and wheel-building logic from something
  like Flit or Whey.

* https://peps.python.org/pep-0517/#build-backend-interface

* https://setuptools.pypa.io/en/latest/build_meta.html#dynamic-build-dependencies-and-other-build-meta-tweaks

* https://github.com/pypa/setuptools/blob/main/setuptools/build_meta.py

Remove Dependency on ``pip``
===============================================================================

* Formula for resolving dependencies and installing packages:
  https://github.com/brettcannon/mousebender

* Tradeoffs with this. More code must be shipped for package handling. More
  code maintenance to keep up with latest PEPs and bug fixes.

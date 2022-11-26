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

* Can use `Dulwich <https://www.dulwich.io/apidocs/>`_, which does not rely on
  Git executable. Will also be more efficient to eliminate subprocess fork-exec
  actions.

More Linters
===============================================================================

* `Fixit <https://github.com/Instagram/Fixit>`_

* `Pylint Utilities <https://github.com/jackdewinter/pylint_utils>`_

* `Ruff <https://github.com/charliermarsh/ruff>`_

* `Sourcery <https://sourcery.ai/>`_

* `Tryceratops <https://github.com/guilatrova/tryceratops>`_

Installable Devshim Wrapper Script
===============================================================================

* Detects whether it is in a devshim-enabled directory tree.

* May also be segue to providing devshim as a package.

* Can just make :file:`develop.py` an installable script and have it act as a
  common interface for execution in-tree or from an installed package.

Restructure Package Dependencies Format
===============================================================================

* Linters, test tools, and other utilities should be optional installation
  dependencies for the Devshim package. Packages which have Devshim as a
  development dependency can specify these options via the ``[]`` syntax.

* Devshim should probe which options have been installed to generate list of
  available commands for direct consumption and for what the metacommands
  (``freshen``, ``lint``, etc...) execute.

* Could consider treating development dependencies as optional installation
  dependencies, as is the practice in parts of the Python community, and could
  then fold into a PEP 621-/PEP 31-compliant :file:`pyproject.toml`. However,
  we would lose the ability to treat comments as TOML lists, as we do now, and
  would not be able to use alternative local paths (from Git submodules, for
  example) for editable package "installation". (Rust's Cargo has the ability
  to get packages from local paths, by preference, and fall back to an index,
  such as crates.io, otherwise. This is very useful and what we want here too.)

Remove Dependency on ``bump2version``
===============================================================================

* Can work directly with ``__version__`` for package and set ``version`` in
  :file:`pyproject.toml` to ``dynamic``.

* Will need to modify project version reader to support the ``dynamic`` field.

* Or maybe use `tbump <https://github.com/your-tools/tbump>`_ as an alternative
  that is ``pyproject.toml``-amenable and has a simpler interface for bumping
  versions.

Remove Dependency on ``invoke``
===============================================================================

* Topological sort of tasks.

* Deduplication of tasks.

* Context managers for task execution.

* Pseudo-TTY support. (May not be necessary.)

* Dynamic passing of arguments to subtasks. (Invoke cannot do this.)

* Surfacing parameters from subtasks.

* Handle via ``develop.py``.

* Possibly use `Typer <https://typer.tiangolo.com/>`_ as partial replacement.

* Async execution fanout. (Nice to have. Limited use cases actually.)

Provide In-Tree PEP 517 Build Backend
===============================================================================

* Proxy to `Enscons <https://pypi.org/project/enscons/>`_?

* Or write our own, borrowing sdist- and wheel-building logic from something
  like Flit or Whey? But would lose Setuptools expertise on compilaton of
  binaries, if needed.

* https://peps.python.org/pep-0517/#build-backend-interface

* https://setuptools.pypa.io/en/latest/build_meta.html#dynamic-build-dependencies-and-other-build-meta-tweaks

Remove Dependency on ``pip``
===============================================================================

* Formula for resolving dependencies and installing packages:
  https://github.com/brettcannon/mousebender

* Tradeoffs with this. More code must be shipped for package handling. More
  code maintenance to keep up with latest PEPs and bug fixes. Unless we can
  pull `*.pyz` files for helper packages, like a dependency resolver and a
  wheel cache manager.

Upstream Bug Reports
===============================================================================

* Mypy: Version >= 0.990 crashes on imports into class namespaces when custom
  metaclass is involved.

* Mypy: Version crashes on dynamic imports from modules that define
  ``__getattr__``.

* Semgrep: No detection of dangerous calls if imported into namespace class.

* YAPF: Uses ``toml`` package which does not support TOML 1 heterogeneous
  lists. Breaks on parsing :file:`pyproject.toml`.

PyPA Discussions of Interest
===============================================================================

* https://discuss.python.org/t/building-distributions-and-drawing-the-platypus/2062

* https://discuss.python.org/t/pep-582-python-local-packages-directory/963

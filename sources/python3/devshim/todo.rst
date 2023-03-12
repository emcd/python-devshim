Fixes and Minor Improvements
===============================================================================

* Python language provider features for Cinder VM and Pyston Lite.
  Install 'sitecustomize.py' files for module auto-loading.
  https://docs.python.org/3/library/site.html

* Add task control argument to support warning/skipping tasks which do not meet
  certain criteria, such as an installation not supporting them.

* Pull from https://github.com/indygreg/python-build-standalone/releases/latest
  for multiple platforms.

* Replace ``build`` with `pyproject-hooks
  <https://github.com/pypa/pyproject-hooks>` for use in both :file:`develop.py`
  and for building sdists and wheels from the package. Removes an additional
  subprocess layer caused by calling ``build`` or ``pip`` and will allow us to
  get around Pip's build tracking when building wheels from source in the build
  support side cache for the CPython TRACEREFS case.

* Add `icecream <https://github.com/gruns/icecream>`_ to development
  dependencies for easier debugging.

* Add `releases <https://github.com/bitprophet/releases>`_ or `towncrier
  <https://github.com/twisted/towncrier>`_ to development dependencies for
  easier changelog management.

Virtual Environments Improvements
================================================================================

* Language Specifiers -> Virtual Environments

* Virtual environments are next layer above language manifestations. May need
  to be aware of some language installation features during virtual environment
  construction.

* Virtual environments are constructed from language manifestation tools.
  Anything installed in virtual environments must be installed by virtual
  environment tools.

Distribution Options
===============================================================================

* Package as zipapp. Then, carve ``develop.py`` down to just find the zipapp,
  downloading it into a cache if necessary, and run it.

* Paves the way for creating standalone executables and ``get-devshim.py``
  scripts (or an alternative ``develop.py`` with a payload, though that is
  probably not SCM-friendly without something like Git LFS enabled).

Restructure Package Dependencies Format
===============================================================================

* Devshim should probe which options have been installed to generate list of
  available commands for direct consumption and for what the metacommands
  (``freshen``, ``lint``, etc...) execute.

* Could consider treating development dependencies as optional installation
  dependencies, as is the practice in parts of the Python community, and could
  then fold into a PEP 621-/PEP 631-compliant :file:`pyproject.toml`. However,
  we would lose the ability to treat comments as TOML lists, as we do now, and
  would not be able to use alternative local paths (from Git submodules, for
  example) for editable package "installation". (Rust's Cargo has the ability
  to get packages from local paths, by preference, and fall back to an index,
  such as crates.io, otherwise. This is very useful and what we want here too.)

More Linters
===============================================================================

* `Codespell <https://github.com/codespell-project/codespell>`_

* `Fixit <https://github.com/Instagram/Fixit>`_

* `Pylint Utilities <https://github.com/jackdewinter/pylint_utils>`_

* `Pytype <https://github.com/google/pytype>`_

* `Ruff <https://github.com/charliermarsh/ruff>`_

* `Sourcery <https://sourcery.ai/>`_

* `Tryceratops <https://github.com/guilatrova/tryceratops>`_

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

Runtime Argument Validation
===============================================================================

* `beartype <https://github.com/beartype/beartype>`_

* `pydantic <https://docs.pydantic.dev/>`_

* `typeguard <https://github.com/agronholm/typeguard>`_

* `typical <https://github.com/seandstewart/typical>`_

Github Actions
===============================================================================

* Write our own PR submitter to reduce supply chain vulnerability.

* Write our own GPG key loader to reduce supply chain vulnerability.
  - https://stackoverflow.com/a/57927025/14833542
  - https://www.gnupg.org/documentation/manuals/gnupg/gpg_002dpreset_002dpassphrase.html
  - https://www.gnupg.org/documentation/manuals/gnupg/Invoking-gpg_002dpreset_002dpassphrase.html#Invoking-gpg_002dpreset_002dpassphrase

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
  pull ``*.pyz`` files for helper packages, like a dependency resolver and a
  wheel cache manager.

PyPA Discussions of Interest
===============================================================================

* https://discuss.python.org/t/building-distributions-and-drawing-the-platypus/2062

* https://discuss.python.org/t/pep-582-python-local-packages-directory/963

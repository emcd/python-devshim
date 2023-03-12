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


Detection of Self
===============================================================================

An ideal goal is to use our own package to detect whether to use an in-tree
or remotely-sourced version of itself. This implies that we would need to
maintain two sets of dependencies, possibly at different versions, in
conjunction with isolated package caches. (Such package caches can be
produced by Pip installs into target directories, for example.) Two sets of
dependencies at different versions further implies a need for import
isolation into separate registries rather than the global 'sys.modules'
registry. Regardless of the project at hand, this is a useful capability to
have, in general. However, there are a number of obstacles to actualizing
this goal, no matter how one attempts to reach it.

Python provides several override mechanisms for its import machinery. For
example, one can create new module finders and register them on
'sys.meta_path', per https://docs.python.org/3/reference/import.html.
These hooks can produce module specs
(https://docs.python.org/3/library/importlib.html#importlib.machinery.ModuleSpec)
that reference module loaders which can load modules from isolated package
caches into isolated module registries instead of 'sys.modules'. However, the
finders and loaders are invoked by the import system driver, the '__import__'
function, which is registered as a Python builtin and called by the Python
language runtime
(https://github.com/python/cpython/blob/v3.11.2/Python/import.c).
This default import hook makes an assumption that 'sys.modules' is the sole
module registry and does not provide a way to use an alternative registry.
One can replace this hook with a customized one, but that, in effect, implies
reimplementation of the bulk of
https://github.com/python/cpython/blob/v3.11.2/Lib/importlib/_bootstrap.py,
which is rather impractical for the return on investment.

Given that the use of import hooks to reach our goal is, in essence, a dead
end, without a very significant investment, another alternative to consider
is whether we can wrap the existing import hook and divert any modules that
it produces into an isolated registry. This is doable, but we must still
provide our own resolution of module names for relative imports, which
involves the duplication and adaptation of a few functions from the default
import driver to support resolution of relative imports, for example. I.e.,
the arguments to '__import__' are not enough to tell us whether we already
have a module in an isolated registry or not.

Another approach is to avoid 'import' statements and use a direct module
loader of our own devising. We do something similar to trigger installation
of our package dependencies via the 'develop.py' module for a project from
callers, such as Sphinx 'conf.py' running on Read The Docs to avoid
maintaining a separate dependencies manifest. However, this only works well
for modules which have no transitive imports. Transitive imports, coming from
the 'import' statement or 'importlib.import_module', will use the registered
import hook and thus not be placed in an isolated registry.

A simpler solution is to challenge our stated goal. If we, instead, accept
that a project maintainer can configure 'develop.py' to point at either an
in-tree version of our package or a remotely-sourced version of our package,
then the above considerations disappear. Does this make 'develop.py' less
portable? Yes. Does this make 'develop.py' less upgradable? Not necessarily.
We can load 'develop.py' as a module and read the maintainer-supplied
configuration to generate an upgraded 'develop.py'.

So, for now, we accept that this entrypoint is for the only implementation of
its package that matters to a project maintainer and that the maintainer has
made a conscious decision to use this implementation. This is simpler than
messing around with import machinery and gives the maintainer more
flexibility about the source of this package at a small cost of 'develop.py'
portability.

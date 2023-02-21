# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Licensed under the Apache License, Version 2.0 (the "License");           #
#   you may not use this file except in compliance with the License.          #
#   You may obtain a copy of the License at                                   #
#                                                                             #
#       http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                             #
#   Unless required by applicable law or agreed to in writing, software       #
#   distributed under the License is distributed on an "AS IS" BASIS,         #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#   See the License for the specific language governing permissions and       #
#   limitations under the License.                                            #
#                                                                             #
###############################################################################


''' Executable entrypoint for package.

    Detects whether it should use an in-tree implementation of its package,
    either from a clone of the source code repository for the package project
    or a Git submodule with such a clone. In-tree implementations are useful
    for development upon the package project itself, either for use on itself
    or another project. Also, making the package executable via the ``-m`` flag
    of the Python interpreter gives users another alternative to running
    ``develop.py``, should they desire. And, lastly, it enables the use of the
    :py:mod:`runpy` from the standard library to be used on the package. '''


# An ideal goal is to use our own package to detect whether to use an in-tree
# or remotely-sourced version of itself. This implies that we would need to
# maintain two sets of dependencies, possibly at different versions, in
# conjunction with isolated package caches. (Such package caches can be
# produced by Pip installs into target directories, for example.) Two sets of
# dependencies at different versions further implies a need for import
# isolation into separate registries rather than the global 'sys.modules'
# registry. Regardless of the project at hand, this is a useful capability to
# have, in general. However, there are a number of obstacles to actualizing
# this goal, no matter how one attempts to reach it.
#
# Python provides several override mechanisms for its import machinery. For
# example, one can create new module finders and register them on
# 'sys.meta_path', per https://docs.python.org/3/reference/import.html#.
# These hooks can produce module specs
# (https://docs.python.org/3/library/importlib.html#importlib.machinery.ModuleSpec)
# that reference module loaders which can load modules from isolated package
# caches into isolated module registries instead of 'sys.modules'. However, the
# finders and loaders are invoked by the import system driver, the '__import__'
# function, which is registered as a Python builtin and called by the Python
# language runtime
# (https://github.com/python/cpython/blob/v3.11.2/Python/import.c#L1736-L1737).
# This default import hook makes an assumption that 'sys.modules' is the sole
# module registry and does not provide a way to use an alternative registry.
# One can replace this hook with a customized one, but that, in effect, implies
# reimplementation of the bulk of
# https://github.com/python/cpython/blob/v3.11.2/Lib/importlib/_bootstrap.py,
# which is rather impractical for the return on investment.
#
# Given that the use of import hooks to reach our goal is, in essence, a dead
# end, without a very significant investment, another alternative to consider
# is whether we can wrap the existing import hook and divert any modules that
# it produces into an isolated registry. This is doable, but we must still
# provide our own resolution of module names for relative imports, which
# involves the duplication and adaptation of a few functions from the default
# import driver to support resolution of relative imports, for example. I.e.,
# the arguments to '__import__' are not enough to tell us whether we already
# have a module in an isolated registry or not.
#
# Another approach is to avoid 'import' statements and use a direct module
# loader of our own devising. We do something similar to trigger installation
# of our package dependencies via the 'develop.py' module for a project from
# callers, such as Sphinx 'conf.py' running on Read The Docs to avoid
# maintaining a separate dependencies manifest. However, this only works well
# for modules which have no transitive imports. Transitive imports, coming from
# the 'import' statement or 'importlib.import_module', will use the registered
# import hook and thus not be placed in an isolated registry.
#
# A simpler solution is to challenge our stated goal. If we, instead, accept
# that a project maintainer can configure 'develop.py' to point at either an
# in-tree version of our package or a remotely-sourced version of our package,
# then the above considerations disappear. Does this make 'develop.py' less
# portable? Yes. Does this make 'develop.py' less upgradable? Not necessarily.
# We can load 'develop.py' as a module and read the maintainer-supplied
# configuration to generate an upgraded 'develop.py'.
#
# So, for now, we accept that this entrypoint is for the only implementation of
# its package that matters to a project maintainer and that the maintainer has
# made a conscious decision to use this implementation. This is simpler than
# messing around with import machinery and gives the maintainer more
# flexibility about the source of this package at a small cost of 'develop.py'
# portability.


# devshim.__main__:
#   * module cache management
#   * must have no standard imports of other parts of devshim;
#     must use cache management instead
#   * must have no standard imports of third-party dependencies;
#     must use cache management instead


def assert_minimum_python_version( ):
    ''' Asserts minimum Python version.

        Checking the Python version must be done in a backwards-compatible
        manner, so as to not trigger syntax exceptions in the checking logic.
        (Compatibility of this logic has been tested back to Python 2.6.) '''
    required_version = 3, 7
    error_message = '\nERROR: Python {0}.{1} or higher required.\n'.format(
        required_version[ 0 ], required_version[ 1 ] )
    from sys import stderr, version_info
    version = version_info[ 0 ], version_info[ 1 ]
    if required_version > version:
        stderr.write( error_message ); stderr.flush( )
        raise SystemExit( 69 ) # EX_UNAVAILABLE

assert_minimum_python_version( )


from contextlib import contextmanager as _context_manager


def add_environment_entry( parts, value ):
    ''' Inserts entry into current process environment.

        Entry name is derived from package name and supplied parts. '''
    from os import environ as current_process_environment
    name = '_'.join( map( str.upper, ( __package__, *parts ) ) )
    current_process_environment[ name ] = str( value )
    return name


def ascertain_package_discovery_location( ):
    ''' Ascertains location from which our package is discoverable. '''
    # TODO: Consider cases where '__file__' may not be set.
    from pathlib import Path
    return Path( __file__ ).parent.parent


def ensure_sanity( project_location = None ):
    ''' Ensures dependency installation. '''
    from pathlib import Path
    # If project location specified, then assume that we should create and use
    # package dependencies relative to the project location. Else, assume
    # current working directory is location for possibly future project or for
    # general command and assume that we are running from an executable that is
    # part of our installation and thus assume no further action is required.
    project_location_ = (
        project_location or Path( ) ).resolve( strict = True )
    add_environment_entry( ( 'project', 'location' ), project_location_ )
    if None is project_location: return None, None
    add_environment_entry( ( 'packages', 'cohort' ), __package__ )
    package_discovery_location = ascertain_package_discovery_location( )
    with imports_from_cache( package_discovery_location ):
        from .pre import ensure_python_packages_cache
        return (
            imports_from_cache( package_discovery_location ),
            imports_from_cache( ensure_python_packages_cache( __package__ ) ) )


def main( project_location = None ):
    ''' Entrypoint for development activity. '''
    ensure_sanity( project_location = project_location )
    with imports_from_cache( ascertain_package_discovery_location( ) ):
        from .pre import ensure_python_packages_cache
        with imports_from_cache( ensure_python_packages_cache( __package__ ) ):
            # pylint: disable=import-error
            from invoke import Collection, Program
            from devshim import tasks
            # pylint: enable=import-error
            Program( namespace = Collection.from_module( tasks ) ).run( )


@_context_manager
def imports_from_cache( location, process_pth_files = False ):
    ''' Context manager for package imports from cache directory. '''
    location_ = str( location )
    if process_pth_files:
        # TODO: Reimplement pth processor from 'site'.
        from site import addsitedir
        addsitedir( location_ )
    from sys import path as modules_discovery_locations
    modules_discovery_locations.insert( 0, location_ )
    yield location
    modules_discovery_locations.remove( location_ )


# Can be invoked in various ways, such as 'runpy.run_path' from inside an
# active interpreter, which uses '<run_path>' as the default module name.
# References:
# * https://peps.python.org/pep-0338/
# * https://docs.python.org/3/library/runpy.html#module-runpy
# * https://docs.python.org/3/using/cmdline.html#cmdoption-m
if __name__ in ( '<run_path>', '__main__' ): main( )

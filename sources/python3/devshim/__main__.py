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

    Ensures that package dependencies are available.

    By default, presents list of available tasks.

    Enables the use of the :py:mod:`runpy` module from the standard library
    with this package. By extension, this also means that the package supports
    the '-m' flag to the Python interpreter. '''


def assert_minimum_python_version( ):
    ''' Asserts minimum Python version.

        Checking the Python version must be done in a backwards-compatible
        manner, so as to not trigger syntax exceptions in the checking logic.
        (Compatibility of this logic has been tested back to Python 2.6.) '''
    required_version = 3, 8
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
    package_discovery_manager, packages_cache_manager = (
        ensure_sanity( project_location = project_location ) )
    from contextlib import ExitStack as CMStack
    with CMStack( ) as contexts:
        contexts.enter_context( package_discovery_manager )
        contexts.enter_context( packages_cache_manager )
        from .user_interface import enhance
        enhance( )
        from invoke import Collection, Program
        from . import tasks
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

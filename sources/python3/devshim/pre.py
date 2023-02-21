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


''' Management of isolated package dependency caches. '''


from . import base as __


def calculate_cache_identifier( ):
    ''' Calculates cache identifier from Python version and platform ID.

        Needs to be unique to not collide with other Python installations
        sharing the same file system. Needs to be shell-safe for use in paths
        and environment variables. Needs to be sensitive to Python or OS
        upgrades to ensure goodness of cache. A hex-encoded cryptographic
        digest of the raw Python version text, the platform uname, and the
        version of this program  meets these requirements handily. '''
    from hashlib import sha256
    from platform import uname
    from sys import version
    hasher = sha256( )
    hasher.update( ''.join( ( version, *uname( ), __.version ) ).encode( ) )
    return hasher.hexdigest( )


def ensure_archives_store( ):
    ''' Ensures directory for retrieved archives exists. '''
    from .fs_utilities import ensure_directory
    # TODO: Use artifacts location from base module after revision.
    return ensure_directory(
        __.Path( __.view_environment_entry( ( 'project', 'location' ) ) )
        .joinpath( f".local/caches/{__package__}/archives" ) )


def ensure_pip( ):
    ''' Ensures existence of recent Pip archive. '''
    archives_location = ensure_archives_store( )
    location = archives_location / 'pip.pyz'
    if location.exists( ):
        from datetime import timedelta as TimeDelta
        from .fs_utilities import is_older_than
        if not is_older_than( location, TimeDelta( days = 1 ) ):
            return location
    retrieve_pip( location )
    return location


def ensure_python_packages( cohort_name, requirements ):
    ''' Ensures all packages in cohort are recent. '''
    location = ensure_python_packages_cache( cohort_name )
    try: next( location.iterdir( ) )
    except StopIteration: pass
    else:
        from datetime import timedelta as TimeDelta
        from .fs_utilities import is_older_than
        if not is_older_than( location, TimeDelta( days = 1 ) ):
            return location
    install_python_packages( location, requirements )
    return location


def ensure_python_packages_cache( cohort_name ):
    ''' Ensures directory for installed Python packages cohort exists. '''
    from .fs_utilities import ensure_directory
    # TODO: Use caches location from base module after revision.
    return ensure_directory(
        __.Path( __.view_environment_entry( ( 'project', 'location' ) ) )
        .joinpath(
            f".local/caches/{__package__}/packages",
            calculate_cache_identifier( ),
            cohort_name ) )


def execute_python_subprocess( command_specification, **nomargs ):
    ''' Executes command with same executable as active interpreter. '''
    from sys import executable as python_location
    command_specification = (
        __.normalize_command_specification( command_specification ) )
    return __.execute_subprocess(
        ( ( python_location, *command_specification ) ), **nomargs )


@__.context_manager
def imports_from_cache( ):
    ''' Context manager for package imports from cache directory. '''
    cohort_name = __.view_environment_entry( ( 'packages', 'cohort' ) )
    if not cohort_name:
        yield
        return
    location = str( ensure_python_packages_cache( cohort_name ) )
    # TODO? Process pth files.
    from sys import path as modules_discovery_locations
    modules_discovery_locations.insert( 0, location )
    yield
    modules_discovery_locations.remove( location )


def install_python_packages( location, requirements ):
    ''' Installs Python packages into directory. '''
    if isinstance( requirements, __.Path ):
        requirements = ( '--requirement', requirements, )
    elif isinstance( requirements, str ):
        requirements = ( requirements, )
    __.scribe.info( f"Installing Python packages to '{location}'." )
    # Force reinstall to help ensure sanity.
    execute_python_subprocess(
        ( ensure_pip( ), 'install', '--target', location,
          '--force-reinstall', '--upgrade', '--upgrade-strategy=eager',
          *requirements ) )


def retrieve_pip( location ):
    ''' Downloads executable Pip archive from Python Packaging Authority. '''
    url = f"https://bootstrap.pypa.io/pip/{location.name}"
    __.scribe.info( f"Retrieving Pip from {url!r}." )
    from .http_utilities import retrieve_url
    retrieve_url( url, location )


def _conditionally_execute( ):
    cohort_name = __.view_environment_entry( ( 'packages', 'cohort' ) )
    # TODO: Decode requirements location from environment.
    if not cohort_name: return
    # TODO: Generate 'packages.exact.pip' programmatically.
    # XXX: Rebuild 'packages.exact.pip' via:
    #   pip-compile \
    #       --generate-hashes \
    #       --output-file sources/python3/devshim/packages.exact.pip \
    #       pyproject.toml
    ensure_python_packages(
        cohort_name, __.Path( __file__ ).parent / 'packages.exact.pip' )

_conditionally_execute( )

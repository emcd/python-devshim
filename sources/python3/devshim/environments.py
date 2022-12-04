# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Development support for virtual environments. '''


# Latent Dependencies:
#   environments -> packages -> environments
# pylint: disable=cyclic-import


def _probe_our_python_environment( ):
    ''' Is execution within Python environment created by this package? '''
    from os import environ as current_process_environment
    return 'OUR_VENV_NAME' in current_process_environment

in_our_python_environment = _probe_our_python_environment( )


def build_python_venv( version, overwrite = False ):
    ''' Creates virtual environment for requested Python version. '''
    from .platforms import detect_vmgr_python_path
    python_path = detect_vmgr_python_path( version )
    from .fs_utilities import ensure_directory
    venv_path = ensure_directory( derive_venv_path( version, python_path ) )
    venv_options = [ ]
    if overwrite: venv_options.append( '--clear' )
    venv_options_str = ' '.join( venv_options )
    from .base import execute_external
    execute_external( f"{python_path} -m venv {venv_options_str} {venv_path}" )
    _install_packages_into_venv( version, venv_path )


def _install_packages_into_venv( version, venv_path ):
    process_environment = derive_venv_variables( venv_path = venv_path )
    from .packages import (
        calculate_python_packages_fixtures,
        install_python_packages,
        record_python_packages_fixtures,
    )
    install_python_packages( process_environment )
    fixtures = calculate_python_packages_fixtures( process_environment )
    from .platforms import pep508_identify_python
    identifier = pep508_identify_python( version = version )
    record_python_packages_fixtures( identifier, fixtures )


def test_package_executable(
    executable_name, process_environment = None, proper_package_name = None
):
    ''' Checks if executable from package is in environment.

        Is a proxy for determining if a package is installed. '''
    from os import environ as current_process_environment
    process_environment = process_environment or current_process_environment
    venv_path = process_environment.get( 'VIRTUAL_ENV' )
    if venv_path and is_executable_in_venv(
        executable_name, venv_path = venv_path
    ): return True
    from shutil import which
    search_path = process_environment.get( 'PATH' )
    if search_path and which( executable_name, path = search_path ):
        return True
    if not proper_package_name:
        proper_package_name = executable_name.capitalize( )
    # TODO: Use logging instead of eprint.
    from .base import eprint
    eprint( f"{proper_package_name} not available. Skipping." )
    return False


def is_executable_in_venv( name, venv_path = None, version = None ):
    ''' Checks if file is executable from virtual environment.

        Preferable over :py:func:`shutil.which` since it will not erroneously
        pick up shims, such as Asdf uses. '''
    from os import F_OK, R_OK, X_OK, access as test_fs_access
    from pathlib import Path
    venv_path = Path( venv_path or derive_venv_path( version = version ) )
    for path in ( venv_path / 'bin' ).iterdir( ):
        if name != path.name: continue
        if test_fs_access( path, F_OK | R_OK | X_OK ): return True
    return False


def venv_execute_external(
    command_specification, venv_specification = None, **nomargs
):
    ''' Executes command in virtual environment subprocess.

        Raises exception on non-zero exit code. '''
    process_environment = derive_venv_variables(
        **( { } if venv_specification is None else venv_specification ) )
    # TODO: Consider if environment is already being passed.
    from .base import execute_external
    return execute_external(
        command_specification, env = process_environment, **nomargs )


def derive_venv_variables(
    venv_path = None, version = None, variables = None
):
    ''' Derives environment variables from Python virtual environment path. '''
    from os import environ as current_process_environment, pathsep
    from pathlib import Path
    venv_path = Path( venv_path or derive_venv_path( version = version ) )
    variables = ( variables or current_process_environment ).copy( )
    variables.pop( 'PYTHONHOME', None )
    variables[ 'PATH' ] = pathsep.join( (
        str( venv_path / 'bin' ), variables[ 'PATH' ] ) )
    variables[ 'VIRTUAL_ENV' ] = str( venv_path )
    variables[ 'OUR_VENV_NAME' ] = venv_path.name
    return variables


def derive_venv_path( version = None, python_path = None ):
    ''' Derives Python virtual environment path from version handle. '''
    from os import environ as current_process_environment
    from pathlib import Path
    cpe = current_process_environment
    required_keys = frozenset( { 'VIRTUAL_ENV', 'OUR_VENV_NAME' } )
    from .platforms import detect_vmgr_python_path
    if None is python_path:
        if version: python_path = detect_vmgr_python_path( version = version )
        elif required_keys == required_keys & cpe.keys( ):
            venv_path = Path( cpe[ 'VIRTUAL_ENV' ] )
            if venv_path.name == cpe[ 'OUR_VENV_NAME' ]: return venv_path
    if None is python_path: python_path = detect_vmgr_python_path( )
    from .platforms import identify_python
    abi_label = identify_python(
        'bdist-compatibility', python_path = python_path )
    from .data import paths
    return paths.environments / abi_label

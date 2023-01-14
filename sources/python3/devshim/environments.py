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

# TODO: Support virtual environments for ABI-incompatible language
#       materializations, such as CPython compiled with the 'TRACEREFS' macro.
#       In the Python TRACEREFS case, one cannot simply install packages with
#       the '--no-binary' option to 'pip install', because Setuptools-driven
#       builds do not inherit that flag, thus picking up build requirements,
#       such as Cython, that are not compatible with the TRACEREFS-imbued
#       interpreter. (A further, more esoteric problem arises when installing
#       build support tools into a side cache that is not part of the virtual
#       environment, as part of building the project package as an editable
#       wheel, and having a published wheel of the project package be a
#       dependency of a tool in the side cache. This upsets Pip build tracking
#       when it is forced to build the wheel, targeting the side cache, from
#       source, as it has already registered the project package as needing to
#       be built from source for installation as an editable wheel in the
#       virtual environment. Using '--no-binary :all:' in conjuction with
#       '--only-binary <whitelist>' does not mitigate the problem, because,
#       although the options are not explicitly mutually-exclusive, the ':all:'
#       cancels the whitelist.) Using packages, such as PyYAML (which is a
#       dependency of a number of important, common packages), that are linked
#       against the standard ABI (i.e., wheels from PyPI), rather than rebuilt
#       from sources, results in a virtual environment that is mostly unusable
#       and therefore also a non-starter.


# Latent Dependencies:
#   environments -> packages -> environments
# pylint: disable=cyclic-import


from . import base as __


def _probe_our_python_environment( ):
    ''' Is execution within Python environment created by this package? '''
    from os import environ as current_process_environment
    return 'OUR_VENV_NAME' in current_process_environment

in_our_python_environment = _probe_our_python_environment( )


def build_python_venv( version, overwrite = False ):
    ''' Creates virtual environment for requested Python version. '''
    from .languages.python import Language
    descriptor = Language.produce_descriptor( version )
    try: python_path = descriptor.infer_executables_location( name = 'python' )
    except Exception: # pylint: disable=broad-except
        __.scribe.error(
            f"Absent or corrupt installation for Python {version!r}." )
        __.scribe.info( f"Reinstalling Python {version!r}." )
        descriptor.install( force = True )
        python_path = descriptor.infer_executables_location( name = 'python' )
    from .fs_utilities import ensure_directory
    venv_path = ensure_directory( derive_venv_path( version, python_path ) )
    venv_options = [ ]
    if overwrite: venv_options.append( '--clear' )
    from .base import execute_external
    execute_external( (
        python_path, '-m', 'virtualenv', *venv_options, venv_path ) )
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
    # TODO: Get PEP 508 platform identity from language descriptor.
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
    if venv_path:
        return is_executable_in_venv( executable_name, venv_path = venv_path )
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
    from .fs_utilities import (
        determine_executable_name_extensions,
        determine_executables_location_part,
    )
    possible_names = determine_executable_name_extensions( name = name )
    executables_part = determine_executables_location_part( )
    try: venv_path = Path( venv_path or derive_venv_path( version = version ) )
    except Exception: return False # pylint: disable=broad-except
    if not venv_path.exists( ): return False
    for path in ( venv_path / executables_part ).iterdir( ):
        if path.name not in possible_names: continue
        if test_fs_access( path, F_OK | R_OK | X_OK ): return True
    return False


def generate_venv_executable_location(
    name, venv_path = None, version = None
):
    ''' Generates expected location of executable in virtual environment. '''
    from pathlib import Path
    from .fs_utilities import determine_executables_location_part
    executables_part = determine_executables_location_part( )
    venv_path = Path( venv_path or derive_venv_path( version = version ) )
    return venv_path / executables_part / name


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
    from .fs_utilities import determine_executables_location_part
    executables_part = determine_executables_location_part( )
    venv_path = Path( venv_path or derive_venv_path( version = version ) )
    variables = ( variables or current_process_environment ).copy( )
    variables.pop( 'PYTHONHOME', None )
    variables[ 'PATH' ] = pathsep.join( (
        str( venv_path / executables_part ), variables[ 'PATH' ] ) )
    variables[ 'VIRTUAL_ENV' ] = str( venv_path )
    variables[ 'OUR_VENV_NAME' ] = venv_path.name
    return variables


def derive_venv_path( version = None, python_path = None ):
    ''' Derives Python virtual environment path from version handle. '''
    from os import environ as current_process_environment
    from pathlib import Path
    cpe = current_process_environment
    required_keys = frozenset( { 'VIRTUAL_ENV', 'OUR_VENV_NAME' } )
    if None is python_path:
        if version: pass
        elif required_keys == required_keys & cpe.keys( ):
            venv_path = Path( cpe[ 'VIRTUAL_ENV' ] )
            if venv_path.name == cpe[ 'OUR_VENV_NAME' ]: return venv_path
    if None is python_path:
        from .languages.python import Language
        python_path = (
            Language.produce_descriptor( version )
            .infer_executables_location( name = 'python' ) )
    from .platforms import identify_python
    abi_label = identify_python(
        'bdist-compatibility', python_path = python_path )
    from .data import paths
    return ( paths.environments / abi_label ).resolve( )


__.reclassify_module( __name__ )

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


''' Management of development platforms. '''


def freshen_python( original_version ):
    ''' Updates supported Python minor version to latest patch.

        This task requires Internet access and may take some time. '''
    minor_version = _derive_python_minor_version( original_version )
    successor_version = _derive_python_complete_version( minor_version )
    from subprocess import SubprocessError # nosec B404
    try:
        original_identifier = pep508_identify_python(
            version = original_version )
    # Version may not be installed.
    except SubprocessError: original_identifier = None
    from ..base import execute_external
    execute_external(
        f"asdf install python {successor_version}", capture_output = False )
    # Do not erase packages fixtures for extant versions.
    successor_identifier = pep508_identify_python(
        version = successor_version )
    if original_identifier == successor_identifier: original_identifier = None
    return { original_version: successor_version }, original_identifier


def _derive_python_complete_version( minor_version ):
    ''' Given a minor version, return the corresponding complete version. '''
    from shlex import split as split_command
    from ..base import execute_external
    return execute_external(
        ( *split_command( 'asdf latest python' ), minor_version )
    ).stdout.strip( )


def _derive_python_minor_version( version ):
    ''' Given a full version, return the corresponding minor version. '''
    from re import compile as regex_compile
    minors_regex = regex_compile(
        r'''^(?P<prefix>\w+(?:\d+\.\d+)?-)?(?P<minor>\d+\.\d+)\..*$''' )
    groups = minors_regex.match( version ).groupdict( )
    return "{prefix}{minor}".format(
        prefix = groups.get( 'prefix' ) or '',
        minor = groups[ 'minor' ] )


def install_python_builder( ):
    ''' Install Python builder utility for platform, if one exists. '''
    from os import name as os_class
    if 'posix' == os_class: install_python_builder_posix( )


def install_python_builder_posix( ):
    ''' Installs 'python-build' utility. '''
    from os import environ as active_process_environment
    environment = active_process_environment.copy( )
    from ..locations import paths
    environment.update( dict( PREFIX = paths.caches.utilities.python_build, ) )
    from ..base import execute_external
    execute_external(
        str( paths.scm_modules.aux.joinpath(
            'pyenv', 'plugins', 'python-build', 'install.sh' ) ),
        env = environment )


def identify_active_python( mode ):
    ''' Reports compatibility identifier for active Python. '''
    from .identity import dispatch_table
    return dispatch_table[ mode ]( )


#: ABI label for executing Python.
active_python_abi_label = identify_active_python( 'bdist-compatibility' )


def pep508_identify_python( version = None ):
    ''' Calculates PEP 508 identifier for Python version. '''
    python_path = detect_vmgr_python_path( version = version )
    return identify_python( 'pep508-environment', python_path = python_path )


def identify_python( mode, python_path ):
    ''' Reports compatibility identifier for Python at given path. '''
    from ..locations import paths
    detector_path = paths.scripts.aux.python3 / 'identify-python.py'
    from ..base import execute_external
    return execute_external(
        ( python_path, detector_path, '--mode', mode ) ).stdout.strip( )


def detect_vmgr_python_path( version = None ):
    ''' Detects Python path using handle from version manager. '''
    version = version or detect_vmgr_python_version( )
    from pathlib import Path
    from shlex import split as split_command
    from ..base import execute_external
    installation_path = Path( execute_external(
        ( *split_command( 'asdf where python' ), version ) ).stdout.strip( ) )
    return installation_path / 'bin' / 'python'


def detect_vmgr_python_version( ):
    ''' Detects Python handle selected by version manager. '''
    # TODO: If in venv, then get active Python version.
    return next( iter( indicate_python_versions_support( ) ) )


def calculate_python_versions( version ):
    ''' Given a Python version specifier, calculate all relevant versions. '''
    if 'ALL' == version: return indicate_python_versions_support( )
    return ( version, )


def indicate_python_versions_support( ):
    ''' Returns supported Python versions. '''
    from os import environ as current_process_environment
    version = current_process_environment.get( 'ASDF_PYTHON_VERSION' )
    if None is not version: return ( version, )
    from re import MULTILINE, compile as regex_compile
    regex = regex_compile( r'''^python\s+(.*)$''', MULTILINE )
    from ..locations import paths
    with paths.configuration.asdf.open( ) as file:
        return regex.match( file.read( ) )[ 1 ].split( )

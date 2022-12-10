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


''' Entrypoint for development activity.

    Bootstraps basic development environment as necessary. '''


_EX_UNAVAILABLE = 69


def assert_minimum_python_version( ):
    ''' Asserts minimum Python version in a version-agnostic manner.

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
        raise SystemExit( _EX_UNAVAILABLE )

assert_minimum_python_version( )


def initialize( ):
    ''' Initializes development support executor. '''
    from logging import (
        INFO as record_level_info,
        basicConfig as simple_setup_logging,
        captureWarnings as capture_admonitions,
        getLogger as get_logger,
    )
    simple_setup_logging( level = record_level_info )
    capture_admonitions( True )
    from pathlib import Path
    project_path = Path( __file__ ).parent
    ensure_scm_modules( project_path )
    configure_auxiliary( project_path )
    from devshim import complete_initialization
    complete_initialization( scribe = get_logger( ) )


def ensure_scm_modules( project_path ):
    ''' Ensures SCM modules have been cloned. '''
    # TODO: Do not hard-code SCM modules paths.
    #       Instead, bootstrap Dulwich first and then scan the registered
    #       submodules of the repository.
    # TODO: Use '.local/scm-modules' only.
    #       Top-level project should not care about 'devshim' SCM modules.
    for modules_path in (
        project_path / '.local' / 'scm-modules',
        project_path / 'scm-modules',
    ):
        if not modules_path.is_dir( ): continue
        for module_path in modules_path.iterdir( ):
            if not module_path.is_dir( ): continue
            if 0 < len( tuple( module_path.iterdir( ) ) ):
                _attempt_clone_scm_modules( project_path )
                return


def _attempt_clone_scm_modules( project_path ):
    ''' Attempts to clone SCM modules. '''
    from shutil import which
    git_path = which( 'git' )
    if None is git_path:
        _die(
            _EX_UNAVAILABLE,
            'Git must be installed to use development support tools.' )
    from logging import info
    info( 'Cloning SCM modules to get development support tools.' )
    from subprocess import run # nosec: B404
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    run( # nosec: B603
        ( git_path, *'submodule update --init --recursive'.split( ' ' ) ),
        capture_output = True, check = True, cwd = project_path, text = True )


def configure_auxiliary( project_path ):
    ''' Locates and configures development support modules. '''
    auxiliary_path = project_path.joinpath(
        '.local', 'scm-modules', 'python-devshim' )
    packages_path = (
        auxiliary_path if auxiliary_path.is_dir( )
        else project_path ) / 'sources' / 'python3'
    from sys import path as python_search_paths
    python_search_paths.insert( 0, str( packages_path ) )
    from os import environ as current_process_environment
    current_process_environment.update( dict(
        _DEVSHIM_PROJECT_PATH = str( project_path ),
    ) )
    from devshim.base import assert_sanity
    assert_sanity( )


def _die( exit_code, message ):
    ''' Logs message and exits with given code. '''
    from logging import critical
    critical( message )
    raise SystemExit( exit_code )


def main( ):
    ''' Entrypoint for development activity. '''
    initialize( )
    from invoke import Collection, Program
    from devshim import tasks
    Program( namespace = Collection.from_module( tasks ) ).run( )


if '__main__' == __name__: main( )

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


''' Fundamental constants and utilities for development support. '''

import typing as _typ

from contextlib import contextmanager as _context_manager


@_context_manager
def springy_chdir( new_path ):
    ''' Changes directory, restoring original directory on context exit. '''
    from os import chdir, getcwd
    old_path = getcwd( )
    chdir( new_path )
    yield new_path
    chdir( old_path )


def _detect_ci_environment( ):
    ''' Returns name of current continuous integration environment.

        If none is detected, returns empty string.

        This is not inteded to be used to Volkswagen test results. '''
    from os import environ as current_process_environment
    if 'CI' in current_process_environment: return 'Github Actions'
    return ''

#: Detected CI environment. Empty string if none detected.
ci_environment = _detect_ci_environment( )


def _probe_tty( ):
    ''' Detects if current process attached to a TTY.

        Boolean result can be used to decide whether to suppress the use of
        ANSI SGR codes for some programs, for example. '''
    from sys import stderr
    # TODO: Check other streams, particularly if streams are merged.
    return stderr.isatty( )

#: Is current process attached to a TTY?
on_tty = _probe_tty( )


def _select_narration_target( ):
    ''' Selects which stream is target for narration and diagnostics. '''
    from sys import stdout, stderr
    # If in CI environment with a buffered pseudo-TTY,
    # then use 'stdout' for properly interleaved output.
    if ci_environment in ( 'Github Actions', ): return stdout
    return stderr

#: Target stream for narration and diagnostics.
narration_target = _select_narration_target( )


def _select_narrative_functions( ):
    ''' Selects which functions to use for narration and diagnostics. '''
    from pprint import pprint
    from sys import stderr
    if stderr is not narration_target: return print, pprint
    from functools import partial as partial_function
    return (
        partial_function( print, file = stderr ),
        partial_function( pprint, stream = stderr ),
    )

eprint, epprint = _select_narrative_functions( )


def execute_external( command_specification, **nomargs ):
    ''' Executes command specification in subprocess.

        Raises exception on non-zero exit code. '''
    options = dict( capture_output = True, text = True )
    from subprocess import STDOUT, run # nosec B404
    from sys import stdout
    options.update( nomargs )
    if not options[ 'capture_output' ] and stdout is narration_target:
        options[ 'stderr' ] = STDOUT
    if { 'stdout', 'stderr' } & options.keys( ):
        options.pop( 'capture_output' )
    options.pop( 'check', None )
    if isinstance( command_specification, str ):
        from shlex import split as split_command
        command_specification = split_command( command_specification )
    # TODO? Handle pseudo-TTY requests with 'ptyprocess.PtyProcess'.
    # TODO? Intercept 'subprocess.SubprocessError'.
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    return run( command_specification, check = True, **options ) # nosec B603


def _enumerate_exit_codes( ):
    from sys import platform
    # TODO: Python 3.10: Use 'match' keyword.
    if platform in ( 'emscripten', 'windows', ):
        return _enumerate_ununixlike_exit_codes( )
    return _enumerate_unixlike_exit_codes( )

def _enumerate_unixlike_exit_codes( ):
    import os
    return {
        'general failure':      1,
        'invalid data':         os.EX_DATAERR,
        'invalid state':        os.EX_SOFTWARE,
        'success':              os.EX_OK,
    }

def _enumerate_ununixlike_exit_codes( ):
    return {
        'general failure':      1,
        'invalid data':         11,
        'invalid state':        31,
        'success':              0,
    }

_exit_codes = _enumerate_exit_codes( )


def expire( exit_name, message ) -> _typ.NoReturn:
    # Preferred name would be 'exit' or 'quit' but those are Python builtins.
    # Could have named it 'die', which is short, sweet, and old school,
    # but other function names are Latin-based whereas 'die' is Germanic.
    # Pet peeve about linguistic consistency....
    ''' Logs message and exits current process. '''
    if exit_name not in _exit_codes:
        scribe.warning( f"Invalid exit code name {exit_name!r}." )
        exit_code = _exit_codes[ 'general failure' ]
    else: exit_code = _exit_codes[ exit_name ]
    message = str( message )
    if 0 == exit_code: scribe.info( message )
    # TODO: Python 3.8: stacklevel = 2
    else: scribe.critical( message, stack_info = True )
    raise SystemExit( exit_code )


def _configure( ):
    ''' Configures development support. '''
    from pathlib import Path
    auxiliary_path = Path( __file__ ).parent.parent.parent.parent
    from os import environ as current_process_environment
    from types import MappingProxyType as DictionaryProxy
    configuration_ = DictionaryProxy( dict(
        auxiliary_path = auxiliary_path,
        project_path = Path( current_process_environment.get(
            '_DEVSHIM_PROJECT_PATH', auxiliary_path ) ),
        scribe = _create_scribe( ),
    ) )
    return configuration_

def _create_scribe( ):
    ''' Initializes logger for package. '''
    from logging import INFO, NullHandler, getLogger as get_logger
    scribe_ = get_logger( __package__ )
    # https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
    scribe_.addHandler( NullHandler( ) )
    from os import environ as current_process_environment
    scribe_.setLevel( current_process_environment.get(
        '_DEVSHIM_RECORD_LEVEL', INFO ) )
    return scribe_

configuration = _configure( )
scribe = configuration[ 'scribe' ]


def assert_sanity( ):
    ''' Assert that operational environment is sane. '''
    # TODO: Implement.

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
from functools import partial as _partial_function
from subprocess import run as _run # nosec


standard_execute_external = _partial_function(
    _run, check = True, capture_output = True, text = True )


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
    if 0 == exit_code: scribe.info( message )
    else: scribe.critical( message, stack_info = True, stacklevel = 2 )
    raise SystemExit( exit_code )


def ensure_directory( path ):
    ''' Ensures existence of directory, creating if necessary. '''
    path.mkdir( parents = True, exist_ok = True )
    return path


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

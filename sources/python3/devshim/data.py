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


''' Common immutable values from deferred computation. '''


import typing as _typ

from . import base as __


# Note: Need to explicitly declare __getattr__-synthesized module attributes
#       to avoid issues with MyPy and Pylint.
paths: _typ.Any
project_name: str
user_directories: _typ.Any


def _provide_calculators( ):
    return dict(
        paths = __.partial_function( _invoke, '.locations.assemble' ),
        project_name = __.partial_function(
            _invoke, '.project.discover_name' ),
        user_directories = __.partial_function(
            _invoke, '.locations.calculate_user_directories' )
    )


def _invoke( name ):
    ''' Imports and executes invocable. '''
    module_name, invocable_name = name.rsplit( sep = '.', maxsplit = 1 )
    from importlib import import_module
    # nosemgrep: python.lang.security.audit.non-literal-import
    module = import_module( module_name, package = __package__ )
    return getattr( module, invocable_name )( )


__getattr__ = __.module_introduce_accretive_cache( _provide_calculators )

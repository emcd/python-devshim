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


# Note: Currently, this is to prevent Mypy from crashing and to avoid having to
#       add this module to Pylint's 'ignored-modules' list.
paths: _typ.Any
project_name: str
user_directories: _typ.Any


def _produce_calculator_names_table( ):
    ''' Produces immutable table of data entries to calculators. '''
    from types import MappingProxyType as DictionaryProxy
    return DictionaryProxy( dict(
        paths            = '.locations.assemble',
        project_name     = '.project.discover_name',
        user_directories = '.locations.calculate_user_directories',
    ) )

_calculator_names = _produce_calculator_names_table( )


# TODO? Python 3.9: Replace with 'functools.cache'.
def _produce_accretive_getattr( ):
    ''' Produces module __getattr__ which caches computed values. '''
    cache = { }

    def module_getattr( name ):
        ''' Returns requested data entry, calculating it if necessary. '''
        if name not in _calculator_names: raise AttributeError
        if name not in cache:
            cache[ name ] = _invoke( _calculator_names[ name ] )
        return cache[ name ]

    return module_getattr


def _invoke( name ):
    ''' Imports and executes invocable. '''
    module_name, invocable_name = name.rsplit( sep = '.', maxsplit = 1 )
    from importlib import import_module
    # nosemgrep: python.lang.security.audit.non-literal-import
    module = import_module( module_name, package = __package__ )
    return getattr( module, invocable_name )( )


__getattr__ = _produce_accretive_getattr( )

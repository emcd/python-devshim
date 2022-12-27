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


''' Utilties for management of Python language installations. '''


import typing as _typ

from types import MappingProxyType as DictionaryProxy

from ...base import module_introduce_accretive_cache
from .. import base as __


# Note: Need to explicitly declare __getattr__-synthesized module attributes
#       to avoid issues with MyPy and Pylint.
locations: _typ.Any
version_definitions: _typ.Any


class Language( __.Language ):
    ''' Manager for Python language. '''

    name = 'python'
    title = 'Python'

    @classmethod
    def provide_version_class( class_ ): return LanguageVersion


class LanguageVersion( __.LanguageVersion ):
    ''' Abstract base for Python language versions. '''

    language = Language

    @classmethod
    def provide_feature_classes_registry( class_ ):
        from .features import reveal_class_registry
        return reveal_class_registry( )

    @classmethod
    def provide_provider_classes_registry( class_ ):
        from .providers import reveal_class_registry # pylint: disable=cyclic-import
        return reveal_class_registry( )

    @classmethod
    def provide_records_location( class_ ):
        return __.locations.data / 'python.toml'

    # TODO: Roll up into base class.
    @classmethod
    def summon_definitions( class_ ):
        return __getattr__( 'version_definitions' )


def _summon_version_definitions( ):
    # TODO? Use 'importlib-resources' to access default definitions.
    from ...packages import ensure_import_package
    tomllib = ensure_import_package( 'tomllib' )
    with ( __.locations.configuration / 'python.toml' ).open( 'rb' ) as file:
        document = tomllib.load( file )
    # TODO: Check format version and dispatch accordingly.
    return DictionaryProxy( document.get( 'versions', { } ) )


def _provide_calculators( ):
    return dict(
        version_definitions = _summon_version_definitions,
    )

__getattr__ = module_introduce_accretive_cache( _provide_calculators )

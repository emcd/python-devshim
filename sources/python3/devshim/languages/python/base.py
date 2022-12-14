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

from lockup import reclassify_module

from ...base import produce_accretive_cacher
from .. import base as __


# Note: Need to explicitly declare __getattr__-synthesized module attributes
#       to avoid issues with MyPy and Pylint.
version_definitions: _typ.Any


class Language( __.Language ):
    ''' Manager for Python language. '''

    name = 'python'
    title = 'Python'

    @classmethod
    def derive_actual_version( class_, version ):
        # TODO: Validate version argument.
        # PEP 440 package versions also seem to hold for Python versions,
        # so we use a package version representation for language versions.
        from packaging.version import Version
        return Version( version )

    @classmethod
    def provide_descriptor_class( class_ ): return LanguageDescriptor

__.register_language( Language )


class LanguageDescriptor( __.LanguageDescriptor ):
    ''' Python language manifestation descriptor. '''

    language = Language

    # TODO: Roll up into base class.
    @classmethod
    def summon_definitions( class_ ):
        return __getattr__( 'version_definitions' )


def _summon_version_definitions( ):
    # TODO? Use 'importlib-resources' to access default definitions.
    from tomli import load as summon
    with ( __.locations.configuration / 'python.toml' ).open( 'rb' ) as file:
        document = summon( file )
    # TODO: Check format version and dispatch accordingly.
    return DictionaryProxy( document.get( 'versions', { } ) )


def _provide_calculators( ):
    return dict(
        version_definitions = _summon_version_definitions,
    )

_data = produce_accretive_cacher( _provide_calculators )
__getattr__ = _data.__getattr__


reclassify_module( __name__ )

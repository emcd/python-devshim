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


# pylint: disable=unused-import
import re

from collections.abc import Mapping as AbstractDictionary
from types import (
    MappingProxyType as DictionaryProxy,
    SimpleNamespace,
)

from ...base import (
    create_immutable_namespace, produce_accretive_cacher, scribe, )
from ...exceptions import provide_exception_factory
# pylint: enable=unused-import
from .. import _base as __


LanguageFeature = __.LanguageFeature
LanguageProvider = __.LanguageProvider
LanguageVersion = __.LanguageVersion


def _calculate_locations( ):
    return create_immutable_namespace( dict(
        # TODO? Use 'importlib-resources' to access default data.
        version_definitions = __.data.locations.configuration / 'python.toml',
        version_records = __.data.locations.state / 'python.toml',
    ) )


def _discover_provider_classes( ):
    from inspect import isclass as is_class
    from . import providers # pylint: disable=cyclic-import
    provider_classes = { }
    for object_ in vars( providers ).values( ):
        if not is_class( object_ ): continue
        if not issubclass( object_, LanguageProvider ): continue
        provider_classes[ object_.name ] = object_
    return DictionaryProxy( provider_classes )


def _summon_version_definitions( ):
    from ...packages import ensure_import_package
    tomllib = ensure_import_package( 'tomllib' )
    with data.locations.version_definitions.open( 'rb' ) as file:
        document = tomllib.load( file )
    # TODO: Check format version and dispatch accordingly.
    return DictionaryProxy( document.get( 'versions', { } ) )


def _produce_calculators( ):
    return dict(
        locations = _calculate_locations,
        provider_classes = _discover_provider_classes,
        version_definitions = _summon_version_definitions,
    )

# TODO: Hoist into separate data module.
data = produce_accretive_cacher( _produce_calculators )

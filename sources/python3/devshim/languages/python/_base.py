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
from types import MappingProxyType as DictionaryProxy

from ...base import produce_accretive_cacher, scribe
from ...exceptions import provide_exception_factory
# pylint: enable=unused-import
from .. import _base as __


def _summon_version_definitions( ):
    from ...data import paths
    from ...packages import ensure_import_package
    tomllib = ensure_import_package( 'tomllib' )
    with paths.configuration.devshim.python.open( 'rb' ) as file:
        document = tomllib.load( file )
    # TODO: Check format version and dispatch accordingly.
    return DictionaryProxy( document.get( 'versions', { } ) )


LanguageFeature = __.LanguageFeature
LanguageProvider = __.LanguageProvider
LanguageVersion = __.LanguageVersion


def _produce_calculators( ):
    return dict(
        version_definitions = _summon_version_definitions,
    )

data = produce_accretive_cacher( _produce_calculators )

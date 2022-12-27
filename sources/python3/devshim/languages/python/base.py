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
from collections.abc import Mapping as AbstractDictionary
from types import (
    MappingProxyType as DictionaryProxy,
    SimpleNamespace,
)

from ...base import (
    create_immutable_namespace,
    module_introduce_accretive_cache,
    scribe,
)
from ...exceptions import provide_exception_factory
from .. import base as __
from ..base import LanguageFeature
# pylint: enable=unused-import


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
        from .providers import reveal_class_registry
        return reveal_class_registry( )

    @classmethod
    def provide_records_location( class_ ):
        from .data import locations
        return locations.version_records

    @classmethod
    def summon_definitions( class_ ):
        from .data import version_definitions
        return version_definitions

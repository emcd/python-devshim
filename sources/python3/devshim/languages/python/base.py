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
    create_immutable_namespace,
    module_introduce_accretive_cache,
    produce_accretive_cacher,
    scribe,
)
from ...exceptions import provide_exception_factory
from ..base import LanguageFeature, LanguageProvider, LanguageVersion
# pylint: enable=unused-import

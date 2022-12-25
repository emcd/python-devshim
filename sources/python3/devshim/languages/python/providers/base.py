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


''' Utilities for Python language providers. '''


# pylint: disable=unused-import
import re

from ....base import (
    create_registrar as _create_registrar,
    produce_accretive_cacher,
)
from ...base import LanguageProvider
# pylint: enable=unused-import


def _validate_class( class_ ):
    from inspect import isclass as is_class
    if not is_class( class_ ) or not issubclass( class_, LanguageProvider ):
        # TODO: Use exception factory.
        raise ValueError
    return class_

register_class, reveal_class_registry = _create_registrar( _validate_class )

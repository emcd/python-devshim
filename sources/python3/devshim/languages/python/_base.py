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

from ...base import scribe
from ...exceptions import provide_exception_factory
# pylint: enable=unused-import
from .. import _base as __


class LanguageContext( __.LanguageContext ):
    ''' Context for Python language version. '''

    def __init__( self, version ): super( ).__init__( 'Python', version )


LanguageProvider = __.LanguageProvider


def normalize_feature_entry( context, entry ):
    ''' Normalizes feature entry from Python version data. '''
    if isinstance( entry, str ):
        return DictionaryProxy( { 'name' : entry } )
    if isinstance( entry, AbstractDictionary ):
        if 'name' in entry: return entry
    raise provide_exception_factory( 'invalid data' )(
        f"Invalid feature entry, {entry!r}, for {context}." )


def normalize_provider_entry( context, entry ):
    ''' Normalizes provider entry from Python version data. '''
    if isinstance( entry, str ):
        return DictionaryProxy( { 'name' : entry } )
    if isinstance( entry, AbstractDictionary ):
        if 'name' in entry: return entry
    raise provide_exception_factory( 'invalid data' )(
        f"Invalid provider entry, {entry!r}, for {context}." )

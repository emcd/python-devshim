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


''' Utilities for management of language installations. '''


from abc import ABCMeta as ABCFactory, abstractmethod as abstract_function
from dataclasses import dataclass


# TODO: Class immutability.
@dataclass( frozen = True )
class LanguageContext( metaclass = ABCFactory ):
    ''' Context for language and version. '''

    language: str
    version: str

    def __str__( self ): return f"{self.language} {self.version}"


# TODO: Class immutability.
class LanguageProvider( metaclass = ABCFactory ):
    ''' Abstract base for language version providers. '''

    @abstract_function
    def install( self ):
        ''' Installs version of language. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @abstract_function
    def attempt_version_data_update( self ):
        ''' Attempts to update version data for version of language. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_base_version( class_, version ):
        ''' Does provider support base version? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_feature( class_, feature ):
        ''' Does provider support feature? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_implementation( class_, implementation ):
        ''' Does provider support implementation? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_platform( class_, platform = None ):
        ''' Does provider support platform? '''
        # TODO: Use exception factory.
        raise NotImplementedError

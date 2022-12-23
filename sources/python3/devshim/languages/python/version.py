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


''' Python versions to install. '''


from . import _base as __


class LanguageVersion( __.LanguageVersion ):
    ''' Abstract base for Python language versions. '''

    def __init__( self, name ): super( ).__init__( 'Python', name )

    @classmethod
    def summon_definitions( class_ ): return __.data.version_definitions

    @classmethod
    def provide_feature_class( class_, name ):
        # TODO: Implement.
        raise NotImplementedError

    @classmethod
    def provide_provider_class( class_, name ):
        # TODO: Cache table of provider classes.
        # TODO: Automatically detect provider classes.
        from .python_build import PythonBuild
        providers = {
            provider.name: provider for provider in ( PythonBuild, ) }
        return providers[ name ]

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


''' Management of special compilation option for reference tracing. '''


from . import base as __


supportable_implementations = ( 'cpython', )


class TraceRefs( __.LanguageFeature ):
    ''' Special compilation option to internally augment Python.

        .. warning:: Incompatible with standard Python binary wheels.

        For CPython, enables compilation with the 'TRACEREFS' macro. '''

    labels = frozenset( ( 'abi-incompatible', 'requires-compilation', ) )
    language = __.Language
    mutex_labels = frozenset( ( 'modifies-interpreter', ) )
    name = 'tracerefs'

    @classmethod
    def is_supportable_base_version( class_, version ):
        # CPython: 'sys.getobjects' not available until version 3.8.
        return ( 3, 8 ) <= tuple( map( int, version.split( '.' ) ) )

    @classmethod
    def is_supportable_implementation( class_, implementation ):
        return implementation in supportable_implementations

    @classmethod
    def is_supportable_platform( class_, platform = None ): return True

    def modify_installation( self, installation_location ): return self

    def modify_provider_environment( self, environment ):
        index = 'PYTHON_CONFIGURE_OPTS'
        environment[ index ] = ' '.join( filter( None,
            ( environment.get( index, '' ), '--with-trace-refs', ) ) )
        return self

__.register_feature_class( TraceRefs )


__.reclassify_module( __name__ )

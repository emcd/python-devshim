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


''' Lazy load utilities. '''


# TODO: Alternative:
#   'devshim.data' subpackage where each module populates on load
#   None of the modules are imported by default.
#
# More Thoughts:
#
#   Locations is a cheap calculation and everything else relies on it.
#   Perform on module import, even if we decide to use a JSON file for
#   the locations hierarchy. Maybe use DictionaryProxy for locations rather
#   than SimpleNamespace. Can create an accessor that recursively changes
#   __getattr__ into dictionary accesses.
#
#   ABI label calculation needs locations and is needed by base package
#   installation. However, it is not expensive with the active Python
#   interpreter that is running the devshim. Therefore, the calculation
#   can also be done on module import.
#
#   Installing base packages is expensive. Only need 'tomli'
#   (until Python 3.11) for many operations. Have a separate 'pre-base'
#   package cache for it. Place the full contingent of base packages
#   into normal 'base' package cache when needed. Provide special loader
#   for these packages rather than adding them to the search path. Will
#   help with isolation when dependent package is the package under
#   development.
class LazyCache:
    ''' Cache which lazily populates its entries. '''

    __slots__ = ( 'loaders', )

    def init( self, loaders ):
        ''' Initialize empty cache with set of available loaders. '''
        # TODO: Validate loaders.
        from types import MappingProxyType as DictionaryProxy
        self._loaders = DictionaryProxy( loaders )
        # TODO: Should be an accretive dictionary.
        self._cache = { }

    def __getattr__( self, name ):
        loader = self._loaders.get( name )
        if None is loader:
            # TODO: Consider early initialization.
            #       Maybe log and raise SystemExit instead.
            raise AttributeError( f"Invalid cache entry {name!r}" )
        if name not in self._cache: self._cache[ name ] = loader( )
        return self._cache[ name ]

    def __setattr__( self, name, value ):
        if not hasattr( self, name ): super( ).__setattr__( name, value )
        # TODO: Consider early initialization.
        #       Maybe log and raise SystemExit instead.
        raise AttributeError(
            f"Attempt to reassign immutable attribute {name!r}" )

    def __delattr__( self, name ):
        # TODO: Consider early initialization.
        #       Maybe log and raise SystemExit instead.
        raise AttributeError(
            f"Attempt to delete indelible attribute {name!r}" )

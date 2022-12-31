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


''' Development support modules. '''


# TODO: __version__


from . import (
    base,
    data,
    environments,
    exceptions,
    file_utilities,
    fs_utilities,
    languages,
    locations,
    packages,
    platforms,
    project,
    scm_utilities,
    tasks,
    user_interface,
)

# TODO: Reclassify each module in its own code.
def _reclassify_modules( ):
    ''' Reclassifies package for attribute concealment and immutability. '''
    from types import ModuleType as Module
    from lockup import reclassify_module
    for attribute in globals( ):
        if not isinstance( attribute, Module ): continue
        if hasattr( attribute, 'complete_initialization' ):
            attribute.complete_initialization( )
        reclassify_module( attribute )
    reclassify_module( __package__ )

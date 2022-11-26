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


''' Management of Python language installations. '''


def survey_versions_support( ):
    ''' Returns declarations of Pythons versions support. '''
    from ...data import paths
    from ...packages import ensure_import_package
    tomllib = ensure_import_package( 'tomllib' )
    with paths.configuration.devshim.python.versions.open( 'rb' ) as file:
        data = tomllib.load( file )
    # TODO: Check format version and dispatch accordingly.
    declarations = data.get( 'versions', { } )
    from os import environ as current_process_environment
    selector = current_process_environment.get( 'DEVSHIM_PYTHON_VERSION' )
    if selector:
        declarations = {
            name: value for name, value in declarations.items( )
            if selector == name
        }
    # TODO: Filter by availability of providers on current OS platform.
    return declarations

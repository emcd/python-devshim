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


''' Management of project. '''


def discover_project_name( ):
    ''' Returns project name, as parsed from local configuration. '''
    return discover_project_information( )[ 'name' ]


def discover_project_version( ):
    ''' Returns project version, as parsed from local configuration. '''
    return discover_project_information( )[ 'version' ]


def discover_project_information( ):
    ''' Discovers information about project from local configuration. '''
    from tomli import load
    from devshim.locations import paths
    with paths.configuration.pyproject.open( 'rb' ) as file:
        tables = load( file )
    information = tables[ 'project' ]
    information.update( tables[ 'tool' ][ 'setuptools' ] )
    information.update( tables[ 'tool' ][ 'SELF' ] )
    return information

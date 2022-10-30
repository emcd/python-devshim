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


''' Management of development platforms. '''


def install_python_builder( ):
    ''' Install Python builder utility for platform, if one exists. '''
    from os import name as os_class
    if 'posix' == os_class: install_python_builder_posix( )


def install_python_builder_posix( ):
    ''' Installs 'python-build' utility. '''
    from os import environ as active_process_environment
    from .base import standard_execute_external
    from .locations import paths
    environment = active_process_environment.copy( )
    environment.update( dict( PREFIX = paths.caches.utilities.python_build, ) )
    standard_execute_external(
        str( paths.scm_modules.aux.joinpath(
            'pyenv', 'plugins', 'python-build', 'install.sh' ) ),
        env = environment )


def identify_active_python( mode ):
    ''' Reports compatibility identifier for active Python. '''
    from devshim__python_identity import dispatch_table
    return dispatch_table[ mode ]( )


# TODO: Add hook for this to an on-demand cache object.
#       Compute only on '__getattr__' for it.
active_python_abi_label = identify_active_python( 'bdist-compatibility' )


def identify_python( mode, python_path ):
    ''' Reports compatibility identifier for Python at given path. '''
    from devshim.locations import paths
    detector_path = paths.scripts.aux.python3 / 'identify-python.py'
    from devshim.base import standard_execute_external
    return standard_execute_external(
        ( python_path, detector_path, '--mode', mode ) ).stdout.strip( )

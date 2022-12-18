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


def identify_active_python( mode ):
    ''' Reports compatibility identifier for active Python. '''
    from .identity import dispatch_table
    return dispatch_table[ mode ]( )


#: ABI label for executing Python.
active_python_abi_label = identify_active_python( 'bdist-compatibility' )


def pep508_identify_python( version = None ):
    ''' Calculates PEP 508 identifier for Python version. '''
    from ..languages.python import infer_executable_location
    python_path = infer_executable_location( version = version )
    return identify_python( 'pep508-environment', python_path = python_path )


def identify_python( mode, python_path ):
    ''' Reports compatibility identifier for Python at given path. '''
    from ..data import paths
    detector_path = paths.scripts.aux.python3 / 'identify-python.py'
    from ..base import execute_external
    return execute_external(
        ( python_path, detector_path, '--mode', mode ),
        capture_output = True ).stdout.strip( )

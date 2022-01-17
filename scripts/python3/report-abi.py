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

''' Reports Python Application Binary Interface (ABI). '''

import platform
import sys

implementation_name = sys.implementation.name
version_mm = '.'.join( map( str, sys.version_info[ : 2 ] ) )
system_type = platform.system( ).lower( )
cpu_architecture = platform.machine( )

if system_type not in ( 'java', 'windows', ):
    system_abi_version = '-'.join( platform.libc_ver( ) )
elif 'java' == system_type:
    # TODO: Implement.
    raise NotImplementedError
elif 'windows' == system_type:
    # TODO: Implement.
    raise NotImplementedError

python_abi_extras = [ ]
if 'cpython' == implementation_name and hasattr( sys, 'getobjects' ):
    python_abi_extras.append( 'trace_refs' )
if 'pypy' == implementation_name:
    python_abi_extras.append(
        '.'.join( map( str, sys.pypy_version_info[ : 2 ] ) ) )
if 'pyston' == implementation_name:
    python_abi_extras.append(
        '.'.join( map( str, sys.pyston_version_info[ : 2 ] ) ) )
if not python_abi_extras: python_abi_extras.append( 'none' )

python_abi_version = "{implementation_name}-{version_mm}-{extras}".format(
    implementation_name = implementation_name,
    version_mm = version_mm,
    extras = '-'.join( python_abi_extras ) )

print( '--'.join( (
    python_abi_version, system_type, system_abi_version, cpu_architecture ) ) )
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


''' Calculates Python compatibility identifiers.

    May be ABI compatibility identifier for binary distributions
    or PEP 508 environment identifier for package installation manifests. '''

# NOTE: This module should not use anything from the package in which it is
#       contained, because it is intended to be run as a standalone script in
#       addition to being a fundamental module for the containing package.

# TODO? Maybe rename to 'derive_*' from 'calculate_*'.


import sys as _sys


implementation_name = _sys.implementation.name


def _determine_prefix( ):
    from pathlib import Path
    if None is __package__: return Path( __file__ ).parent.parent.name
    return __package__.split( '.', maxsplit = 1 )[ 0 ]

_prefix = _determine_prefix( )


def calculate_bdist_compatibility_identifier( ):
    ''' Returns summary identifier for binary distribution compatibility. '''
    return '--'.join( (
        calculate_python_abi_identifier( ),
        calculate_platform_identifier( ),
    ) )


def extract_cpu_identifier( ):
    ''' Extracts and normalizes identifier for CPU architecture. '''
    from os import environ as current_process_environment
    from platform import machine as query_cpu_architecture
    architecture = current_process_environment.get(
        f"{_prefix}_CPU_ARCHITECTURE",
        query_cpu_architecture( ) ).lower( )
    # TODO: Normalize. E.g. aarch64 -> arm64, amd64 -> x86-64
    return architecture


def extract_os_class( ):
    ''' Extracts OS class. (I.e., POSIX or NT.) '''
    from os import environ as current_process_environment, name
    return current_process_environment.get(
        f"{_prefix}_OS_CLASS", name ).lower( )


def calculate_platform_identifier( ):
    ''' Calculates platform name from OS kernel and CPU architecture. '''
    # TODO? Process flag to make complete system ABI identifier
    #       with relevant C library or language VM name.
    from os import environ as current_process_environment
    from platform import (
        architecture as query_os_kernel_architecture,
        system as query_os_kernel_name,
    )
    cpu_architecture = extract_cpu_identifier( )
    os_kernel_architecture = query_os_kernel_architecture( )
    os_kernel_name = current_process_environment.get(
        f"{_prefix}_OS_KERNEL_NAME",
        query_os_kernel_name( ) ).lower( )
    os_kernel_address_size = current_process_environment.get(
        f"{_prefix}_OS_KERNEL_ADDRESS_SIZE",
        os_kernel_architecture[ 0 ] ).lower( )
    os_kernel_specifier = '-'.join( filter( None, (
        os_kernel_name, os_kernel_address_size ) ) )
    return '--'.join( ( os_kernel_specifier, cpu_architecture ) )


def calculate_python_abi_identifier( ):
    ''' Python implementation name, version, and extra ABI differentiators. '''
    return '-'.join( (
        implementation_name,
        format_version( _sys.version_info, 2 ),
        *calculate_python_abi_extras( ) ) )


def calculate_python_abi_extras( ):
    ''' Special builds and variant implementation version. '''
    python_abi_extras = [ ]
    if 'cpython' == implementation_name:
        if hasattr( _sys, 'getobjects' ):
            python_abi_extras.append( 'tracerefs' )
    elif 'pypy' == implementation_name:
        python_abi_extras.append(
            format_version( _sys.pypy_version_info, 2 ) ) # pylint: disable=no-member
    elif 'pyston' == implementation_name:
        python_abi_extras.append(
            format_version( _sys.pyston_version_info, 2 ) ) # pylint: disable=no-member
    return python_abi_extras


def calculate_system_abi_identifier( ):
    ''' System library linkage and virtual machine information. '''
    import platform
    system_type = platform.system( ).lower( )
    if system_type not in ( 'java', 'windows', ):
        return '-'.join( platform.libc_ver( ) )
    if 'windows' == system_type:
        return '-'.join( (
            *reversed( platform.architecture( ) ),
            platform.win32_ver( )[ 1 ] ) )
    # TODO: Implement: java
    # TODO: Implement: emscripten/wasi
    raise NotImplementedError


def calculate_pep508_environment_identifier( ):
    ''' Calculates complete identifier for Python package constraints.

        Identifiers chosen in accordance with `PEP 508 environment markers
        <https://www.python.org/dev/peps/pep-0508/#environment-markers>`. '''
    return '--'.join( (
        calculate_pep508_python_identifier( ),
        calculate_platform_identifier( ),
    ) )


def calculate_pep508_python_identifier( ):
    ''' Python implementation name and version and general version. '''
    return '-'.join( filter( None, (
        implementation_name,
        format_version( _sys.version_info ),
        calculate_pep508_implementation_version( ) ) ) )


def calculate_pep508_implementation_version( ):
    ''' Variant implementation version. '''
    if 'pypy' == implementation_name:
        return format_version( _sys.pypy_version_info ) # pylint: disable=no-member
    if 'pyston' == implementation_name:
        return format_version( _sys.pyston_version_info ) # pylint: disable=no-member
    return ''


def format_version( info, specificity = 'full' ):
    ''' Formats standard named tuple for version into text. '''
    # Full specificity algorithm adapted from
    # https://www.python.org/dev/peps/pep-0508/#environment-markers
    if 'full' == specificity:
        version = '.'.join( map( str, info[ : 3 ] ) )
        release_level = info.releaselevel
        if 'final' != release_level:
            return "{version}{release_level}{serial}".format(
                version = version,
                release_level = release_level[ 0 ],
                serial = info.serial )
        return version
    return '.'.join( map( str, info[ : specificity ] ) )


from types import MappingProxyType as _DictionaryProxy
dispatch_table = _DictionaryProxy( {
    'bdist-compatibility':  calculate_bdist_compatibility_identifier,
    'pep508-environment':   calculate_pep508_environment_identifier,
} )


def main( ):
    ''' Prints identifier label for active Python process. '''
    _setup_python_search_paths( )
    from argparse import ArgumentParser
    cli_parser = ArgumentParser( )
    cli_parser.add_argument( '--mode',
        default = 'bdist-compatibility', metavar = 'MODE',
        choices = dispatch_table.keys( )
    )
    cli_arguments = cli_parser.parse_args( )
    print( dispatch_table[ cli_arguments.mode ]( ) )


def _setup_python_search_paths( ):
    from pathlib import Path
    from sys import path as python_search_paths
    common_path = Path( __file__ ).parent.parent.parent
    python_search_paths.insert( 0, str( common_path / 'sources' / 'python3' ) )


if '__main__' == __name__: main( )
else:
    from lockup import reclassify_module as _reclassify_module
    _reclassify_module( __name__ )

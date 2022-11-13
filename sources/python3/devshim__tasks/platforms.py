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


from lockup import NamespaceClass as _NamespaceClass
class __( metaclass = _NamespaceClass ):

    from subprocess import CalledProcessError as ProcessInvocationError # nosec

    from lockup import reclassify_module


def freshen_python( context, original_version ):
    ''' Updates supported Python minor version to latest patch.

        This task requires Internet access and may take some time. '''
    from devshim.user_interface import render_boxed_title
    render_boxed_title(
        'Freshen: Python Version', supplement = original_version )
    minor_version = _derive_python_minor_version( original_version )
    from shlex import split as split_command
    from devshim.base import standard_execute_external
    successor_version = standard_execute_external(
        ( *split_command( 'asdf latest python' ), minor_version )
    ).stdout.strip( )
    from devshim.platforms import pep508_identify_python
    try:
        original_identifier = pep508_identify_python(
            version = original_version )
    # Version may not be installed.
    except __.ProcessInvocationError: original_identifier = None
    context.run( f"asdf install python {successor_version}", pty = True )
    # Do not erase packages fixtures for extant versions.
    successor_identifier = pep508_identify_python(
        version = successor_version )
    if original_identifier == successor_identifier: original_identifier = None
    return { original_version: successor_version }, original_identifier


def _derive_python_minor_version( version ):
    ''' Given a full version, return the corresponding minor version. '''
    from re import compile as regex_compile
    minors_regex = regex_compile(
        r'''^(?P<prefix>\w+(?:\d+\.\d+)?-)?(?P<minor>\d+\.\d+)\..*$''' )
    groups = minors_regex.match( version ).groupdict( )
    return "{prefix}{minor}".format(
        prefix = groups.get( 'prefix' ) or '',
        minor = groups[ 'minor' ] )


__.reclassify_module( __name__ )

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


''' Filesystem utilities for development support. '''


from . import base as __


def determine_executable_name_extensions( name = None ):
    ''' Determines possible executable name extensions for platform.

        For POSIX platforms, this is an empty tuple. '''
    from .platforms.identity import extract_os_class
    os_class = extract_os_class( )
    if 'nt' == os_class:
        extensions = tuple( map(
            str.lower,
            __.current_process_environment.get(
                'PATHEXT',
                '.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC' )
            .split( ';' ) ) )
    else: extensions = ( '', )
    if None is name: return extensions
    return tuple( map( lambda ext: f"{name}{ext}", extensions ) )


def determine_executables_location_part( ):
    ''' Determines standard executables location indicator for platform. '''
    from .platforms.identity import extract_os_class
    os_class = extract_os_class( )
    if 'nt' == os_class: return 'Scripts'
    return 'bin'


def ensure_directory( path ):
    ''' Ensures existence of directory, creating if necessary. '''
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    path.mkdir( parents = True, exist_ok = True )
    return path


def extract_tarfile( source, destination, selector = None ):
    ''' Extracts tar archive from source into destination.

        The source may be a path-like object or an open stream. An open stream
        will be written to a temporary file, because filtration of archive
        members requires the ability to seek, which not all streams have.

        The destination must be the path to a directory on the file system.

        By default, all members of an archive are extracted. Optionally, a
        sequence or a callable can be used to select members. '''
    from collections.abc import Sequence as AbstractSequence
    from contextlib import ExitStack as ContextStack
    from pathlib import Path
    from tarfile import open as open_tarfile
    from tempfile import NamedTemporaryFile
    if isinstance( selector, AbstractSequence ):
        selector = lambda member: member in selector
    #elif callable( selector ): pass
    # TODO: Else, error.
    contexts = ContextStack( )
    with contexts:
        if isinstance( source, ( str, Path ) ): pass
        elif hasattr( source, 'read' ) and callable( source.read ):
            tempfile = contexts.enter_context( NamedTemporaryFile( ) )
            tempfile.write( source.read( ) )
            source = tempfile.name
        # TODO: Error if source is not path-like.
        tarball = contexts.enter_context( open_tarfile( name = source ) )
        members = tuple( filter( selector, tarball.getmembers( ) ) )
        tarball.extractall( path = destination, members = members )
    return members


def is_older_than( path, then ):
    ''' Is file system entity older than delta time from now? '''
    from datetime import (
        datetime as DateTime, timedelta as TimeDelta, timezone as TimeZone, )
    if isinstance( then, DateTime ): when = then.timestamp( )
    elif isinstance( then, TimeDelta ):
        when = ( DateTime.now( TimeZone.utc ) - then ).timestamp( )
    else:
        when = None
        __.fuse_exception_classes( ( TypeError, ValueError, ) )(
            "Argument 'then' to function 'is_older_than' "
            "must be a datetime or time delta instance "
            "from module 'datetime'." )
    # Windows apparently does not track file metadata change time (ctime);
    # instead file birth time is substituted for ctime on that platform.
    # Therefore, we rely on file content modification time (mtime).
    # This provides the desired behavior in nearly all cases anyway.
    return path.stat( ).st_mtime < when


def unlink_recursively( path ):
    ''' Pure Python implementation of ``rm -rf``, essentially.

        Different than :py:func:`shutil.rmtree` in that it will also
        delete a regular file or symlink as the top-level target
        and it will silently succeed if the top-level target is missing. '''
    if not path.exists( ): return
    if not path.is_dir( ):
        path.unlink( )
        return
    dirs_stack = [ path ]
    for child_path in path.rglob( '*' ):
        if child_path.is_dir( ) and not child_path.is_symlink( ):
            dirs_stack.append( child_path )
            continue
        child_path.unlink( )
    while dirs_stack: dirs_stack.pop( ).rmdir( )

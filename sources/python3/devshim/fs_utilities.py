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


def ensure_directory( path ):
    ''' Ensures existence of directory, creating if necessary. '''
    path.mkdir( parents = True, exist_ok = True )
    return path


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

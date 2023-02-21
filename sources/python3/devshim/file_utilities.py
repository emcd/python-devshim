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

''' Utilities for file calculations and manipulation. '''


from . import base as __


def gpg_sign_file( path ):
    ''' Generates detached, ASCII-armored GPG signature for file. '''
    assert_gpg_tty( )
    __.execute_external( f"gpg --yes --detach-sign --armor {path}" )


def assert_gpg_tty( ):
    ''' Ensures the the 'GPG_TTY' environment variable is set. '''
    if 'GPG_TTY' in __.current_process_environment: return
    # TODO: Check for cached passphrase as an alternative.
    # TODO: Use exception factory.
    raise RuntimeError(
        "ERROR: Environment variable 'GPG_TTY' is not set. "
        "Task cannot prompt for GPG secret key passphrase." )

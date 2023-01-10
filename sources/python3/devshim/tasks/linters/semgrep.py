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


''' Task for R2C Semgrep Linter: https://r2c.dev/#semgrep '''


from . import base as __


def update_rules( ):
    ''' Update local copy of Semgrep Rules repository, if necessary. '''
    from datetime import timedelta as TimeDelta
    from pathlib import Path
    from shutil import move, rmtree
    from tempfile import TemporaryDirectory
    from ...data import locations, user_directories
    from ...fs_utilities import extract_tarfile, is_older_than
    from ...scm_utilities import github_retrieve_tarball
    installation_location = (
        user_directories.installations / 'semgrep-rules' )
    repository_location = (
        locations.caches.DEV.repositories / 'semgrep-rules.tar.gz' )
    if repository_location.exists( ):
        # TODO: Configurable refresh time.
        if not is_older_than( repository_location, TimeDelta( days = 1 ) ):
            if installation_location.exists( ): return installation_location
    github_retrieve_tarball(
        'returntocorp/semgrep-rules', 'develop', repository_location )
    with TemporaryDirectory( ) as temporary_location:
        temporary_location = Path( temporary_location )
        members = extract_tarfile( repository_location, temporary_location )
        source_location = temporary_location.joinpath(
            Path( next( iter( members ) ).name ).parts[ 0 ] )
        if installation_location.exists( ): rmtree( installation_location )
        move( source_location, installation_location )
    return installation_location


__.reclassify_module( __name__ )

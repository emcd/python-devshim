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


''' Utilities for source code management (SCM). '''


def github_retrieve_tarball( repository_qname, git_ref, destination ):
    ''' Retrieves tarball for Git repository and ref into destination.

        The repository qualified name is the owner name plus the repository
        name. The ref must be a valid Git ref accepted by the Github API call:
        https://docs.github.com/en/rest/repos/contents#download-a-repository-archive-tar

        The desination may be a path-like object, an open stream, or a callable
        which consumes a stream as its only required positional argument. '''
    from contextlib import ExitStack as ContextStack
    from io import RawIOBase
    from pathlib import Path
    from urllib.request import Request as HttpRequest, urlopen as access_url
    http_request = HttpRequest(
        # TODO: Fix redirect handling.
        #"https://api.github.com/repos/{repository_qname}/tarball/{git_ref}",
        f"https://codeload.github.com/{repository_qname}/legacy.tar.gz/"
        f"refs/heads/{git_ref}",
        headers = { 'Accept': 'application/vnd.github+json' } )
    contexts = ContextStack( )
    # TODO: Handle retries for some error conditions.
    # TODO: Place this as generalized logic in a separate utilities module.
    with contexts:
        http_reader = contexts.enter_context( access_url( http_request ) ) # nosemgrep: scm-modules.semgrep-rules.python.lang.security.audit.dynamic-urllib-use-detected
        if isinstance( destination, ( str, Path ) ):
            tarball_path = Path( destination )
            if not tarball_path.parent.exists( ):
                tarball_path.parent.mkdir( parents = True )
            tarball = contexts.enter_context( tarball_path.open( 'wb' ) )
            tarball.write( http_reader.read( ) )
        # TODO: Look for 'read' method rather than RawIOBase.
        elif isinstance( destination, RawIOBase ):
            destination.write( http_reader.read( ) )
        elif callable( destination ): destination( http_reader )
        # TODO: Else, error.

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

        See the documentation of
        :py:class:`devshim.http_utilities.retrieve_url` for possible values of
        the destination argument. '''
    from .http_utilities import retrieve_url
    #"https://api.github.com/repos/{repository_qname}/tarball/{git_ref}",
    retrieve_url(
        f"https://codeload.github.com/{repository_qname}/legacy.tar.gz/"
        f"refs/heads/{git_ref}",
        destination,
        headers = { 'Accept': 'application/vnd.github+json' } )

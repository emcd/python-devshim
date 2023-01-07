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


''' Utilities for Python language installation providers. '''


# pylint: disable=unused-import
import re

from shlex import split as split_command
from types import MappingProxyType as DictionaryProxy

from lockup import reclassify_module

from ....base import execute_external, produce_accretive_cacher
from ...base import LanguageProvider, register_provider_class
from ..base import Language
# pylint: enable=unused-import


def ensure_site_packages( installation_location, python_location ):
    ''' Ensures standard collection of site packages in installation. '''
    pip_installer_location = (
        retrieve_pip_installer( installation_location ) )
    execute_external(
        ( python_location, pip_installer_location, ),
        cwd = installation_location )
    execute_external(
        ( python_location, *split_command( '-m pip install virtualenv' ), ),
        cwd = installation_location )


def retrieve_pip_installer( installation_location ):
    ''' Fetches 'get-pip.py' to bootstrap Pip installation. '''
    # TODO: Used generalized URL retriever.
    # TODO: Use cached copy if sufficiently recent.
    from contextlib import ExitStack as ContextStack
    from urllib.request import (
        Request as HttpRequest, urlopen as access_url, )
    installer_location = installation_location / 'get-pip.py'
    contexts = ContextStack( )
    # Note: Could use 'pip.pyz' instead, but that is experimental and would
    #       still require a proper Pip installation afterwards.
    http_request = HttpRequest( 'https://bootstrap.pypa.io/get-pip.py' )
    with contexts:
        http_reader = contexts.enter_context( access_url( http_request ) ) # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected
        # TODO: Handle retries.
        installer = contexts.enter_context( installer_location.open( 'wb' ) )
        installer.write( http_reader.read( ) )
    return installer_location


reclassify_module( __name__ )

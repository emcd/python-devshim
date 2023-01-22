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

from types import MappingProxyType as DictionaryProxy

from lockup import reclassify_module

from ....base import (
    create_invocable_dictionary,
    create_semelfactive_namespace,
    execute_external,
)
from ....http_utilities import retrieve_url as http_retrieve_url
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
        ( python_location, *'-m pip install virtualenv'.split( ), ),
        cwd = installation_location )


def retrieve_pip_installer( installation_location ):
    ''' Fetches 'get-pip.py' to bootstrap Pip installation. '''
    # TODO: Use cached copy if sufficiently recent.
    # Note: Could use 'pip.pyz' instead, but that is experimental and would
    #       still require a proper Pip installation afterwards.
    installer_location = installation_location / 'get-pip.py'
    http_retrieve_url(
        'https://bootstrap.pypa.io/get-pip.py', installer_location )
    return installer_location


reclassify_module( __name__ )

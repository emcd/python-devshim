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


''' Development support modules. '''


__version__ = '1.0a202301141418'


# If bootstrapping, then need access to isolated packages cache.
from . import pre
with pre.imports_from_cache( ):
    from . import (
        __main__ as entrypoint,
        base,
        data,
        environments,
        exceptionality,
        file_utilities,
        fs_utilities,
        languages,
        locations,
        packages,
        platforms,
        project,
        scm_utilities,
        tasks,
        user_interface,
    )


# TODO: Backport this function to 'lockup' package.
def _reclassify_modules_by_package_name( *package_names ):
    from sys import modules
    with pre.imports_from_cache( ):
        from lockup import reclassify_module
    prefixes = tuple( f"{package_name}." for package_name in package_names )
    for module_name, module in modules.items( ):
        if module_name in package_names or module_name.startswith( prefixes ):
            reclassify_module( module )

_reclassify_modules_by_package_name( __package__ )

# TODO: Make registered classes immutable.

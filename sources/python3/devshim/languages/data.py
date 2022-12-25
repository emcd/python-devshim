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


''' Latent immutable values for language support. '''


import typing as _typ

from . import base as __


# Note: Need to explicitly declare __getattr__-synthesized module attributes
#       to avoid issues with MyPy and Pylint.
locations: _typ.Any


def _calculate_locations( ):
    from ..data import locations as base_locations
    return __.create_immutable_namespace( dict(
        configuration = base_locations.configuration.DEV.SELF / 'languages',
        state = base_locations.state.DEV.SELF / 'languages',
    ) )


def _provide_calculators( ):
    return dict(
        locations = _calculate_locations,
    )

__getattr__ = __.module_introduce_accretive_cache( _provide_calculators )

# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Licensed under the Apache License, Version 2.0 (the "License");           #
#   you may not use this file except in compliance with the License.          #
#   You may obtain a copy of the License at                                   #
#                                                                             #
#       http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                             #
#   Unless required by applicable law or agreed to in writing, software       #
#   distributed under the License is distributed on an "AS IS" BASIS,         #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#   See the License for the specific language governing permissions and       #
#   limitations under the License.                                            #
#                                                                             #
###############################################################################


''' Conveniences for working with Hypertext Transfer Protocol. '''


from . import base as __


def retrieve_url( url, destination = None, headers = None ): # pylint: disable=too-many-statements
    ''' Retrieves URL into destination via Hypertext Transfer Protocol.

        The destination may be a path-like object, an object with a ``write``
        method, such as an open stream, or a callable which consumes a stream
        from an object with a ``read`` method. The callable must take two
        positional arguments, which will be the HTTP reader object and the
        context stack that ensures proper resource cleanup. '''
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    from random import random
    from time import sleep
    from urllib.error import HTTPError as HttpError
    from urllib.request import Request as HttpRequest
    destination = _normalize_retrieval_destination( destination )
    headers = headers or { } # TODO: Validate headers.
    request = HttpRequest( url, headers = headers )
    attempts_count_max = 2
    for attempts_count in range( attempts_count_max + 1 ):
        try: return _retrieve_url( request, destination )
        except HttpError as exc:
            __.scribe.error( f"Failed to retrieve data from {url!r}." )
            # Exponential backoff with collision-breaking jitter.
            backoff_time = 2 ** attempts_count + 2 * random( ) # nosec: B311
            # https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml
            if exc.code in ( 301, 302, 307, 308 ):  # Redirects
                if 'Location' in exc.headers:
                    url = exc.headers[ 'Location' ]
                    return retrieve_url( url, destination, headers )
                raise
            if 404 == exc.code: raise               # Not Found
            if 429 == exc.code:                     # Too Many Requests
                backoff_time = float(
                    exc.headers.get( 'Retry-After', backoff_time ) )
                if 120 < backoff_time: raise # Do not wait too long.
            if attempts_count_max == attempts_count: raise
            __.scribe.info(
                f"Will attempt retrieval from {url!r} again "
                f"in {backoff_time} seconds." )
            sleep( backoff_time )
    raise __.fuse_exception_classes( ( RuntimeError, ) )(
        'Wut? Unexpectedly fell out of HTTP retrieval retry loop.' )

def _retrieve_url( request, destination ):
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    from contextlib import ExitStack as ContextStack
    from urllib.request import urlopen as access_url
    contexts = ContextStack( )
    with contexts:
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected
        http_reader = contexts.enter_context( access_url( request ) )
        if None is destination: return http_reader.read( )
        if callable( destination ): return destination( http_reader, contexts )
        if isinstance( destination, __.Path ):
            file = contexts.enter_context( destination.open( 'wb' ) )
            file.write( http_reader.read( ) )
        elif callable( getattr( destination, 'write', None ) ):
            destination.write( http_reader.read( ) )
        return destination


def _normalize_retrieval_destination( destination ):
    if isinstance( destination, str ): destination = __.Path( destination )
    if isinstance( destination, __.Path ) and not destination.exists( ):
        destination.parent.mkdir( exist_ok = True, parents = True )
    if not any( (
        None is destination,
        isinstance( destination, __.Path ),
        callable( getattr( destination, 'write', None ) ),
        callable( destination )
    ) ):
        __.fuse_exception_classes( ( ValueError, ) )(
            "Cannot use instance of {class_name!r} "
            "as retrieval destination.".format(
                class_name = __.derive_class_fqname( type( destination ) ) ) )
    return destination

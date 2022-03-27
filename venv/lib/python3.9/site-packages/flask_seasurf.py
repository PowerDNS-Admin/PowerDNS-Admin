'''
    flaskext.seasurf
    ----------------

    A Flask extension providing fairly good protection against cross-site
    request forgery (CSRF), otherwise known as "sea surf".

    :copyright: (c) 2011 by Max Countryman.
    :license: BSD, see LICENSE for more details.
'''

from __future__ import absolute_import

__version_info__ = ('0', '2', '2')
__version__ = '.'.join(__version_info__)
__author__ = 'Max Countryman'
__license__ = 'BSD'
__copyright__ = '(c) 2011 by Max Countryman'
__all__ = ['SeaSurf']

import sys
import hashlib
import random

from datetime import timedelta

from flask import _app_ctx_stack, abort, current_app, request, session
from werkzeug.security import safe_str_cmp


if sys.version_info[0] < 3:
    import urlparse
    _MAX_CSRF_KEY = long(2 << 63)
else:
    import urllib.parse as urlparse
    _MAX_CSRF_KEY = 2 << 63


if hasattr(random, 'SystemRandom'):
    randrange = random.SystemRandom().randrange
else:
    randrange = random.randrange

REASON_NO_REFERER = u'Referer checking failed: no referer.'
REASON_BAD_REFERER = u'Referer checking failed: {0} does not match {1}.'
REASON_NO_CSRF_TOKEN = u'CSRF token not set.'
REASON_BAD_TOKEN = u'CSRF token missing or incorrect.'


def _same_origin(url1, url2):
    '''
    Determine if two URLs share the same origin.

    :param url1: The first URL to compare.
    :param url2: The second URL to compare.
    '''
    p1, p2 = urlparse.urlparse(url1), urlparse.urlparse(url2)
    origin1 = p1.scheme, p1.hostname, p1.port
    origin2 = p2.scheme, p2.hostname, p2.port
    return origin1 == origin2


class SeaSurf(object):
    '''
    Primary class container for CSRF validation logic. The main function of
    this extension is to generate and validate CSRF tokens. The design and
    implementation of this extension is influenced by Django's CSRF middleware.

    Tokens are generated using a salted SHA1 hash. The salt is based off a
    a random range. The OS's SystemRandom is used if available, otherwise
    the core random.randrange is used.

    You might intialize :class:`SeaSurf` something like this::

        csrf = SeaSurf()

    Then pass the application object to be configured::

        csrf.init_app(app)

    Validation will now be active for all requests whose methods are not GET,
    HEAD, OPTIONS, or TRACE.

    When using other request methods, such as POST for instance, you will need
    to provide the CSRF token as a parameter. This can be achieved by making
    use of the Jinja global. In your template::

        <form method="POST">
        ...
        <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
        </form>

    This will assign a token to both the session cookie and the rendered HTML
    which will then be validated on the backend. POST requests missing this
    field will fail unless the header X-CSRFToken is specified.

    .. admonition:: Excluding Views From Validation

        For views that use methods which may be validated but for which you
        wish to not run validation on you may make use of the :class:`exempt`
        decorator to indicate that they should not be checked.
    '''

    def __init__(self, app=None):
        self._exempt_views = set()
        self._include_views = set()
        self._exempt_urls = tuple()

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        '''
        Initializes a Flask object `app`, binds CSRF validation to
        app.before_request, and assigns `csrf_token` as a Jinja global.

        :param app: The Flask application object.
        '''

        app.before_request(self._before_request)
        app.after_request(self._after_request)

        # Expose the CSRF token to the template.
        app.jinja_env.globals['csrf_token'] = self._get_token

        self._csrf_name = app.config.get('CSRF_COOKIE_NAME', '_csrf_token')
        self._csrf_header_name = app.config.get('CSRF_HEADER_NAME',
                                                'X-CSRFToken')
        self._csrf_disable = app.config.get('CSRF_DISABLE',
                                            app.config.get('TESTING', False))
        self._csrf_timeout = app.config.get('CSRF_COOKIE_TIMEOUT',
                                            timedelta(days=5))
        self._csrf_secure = app.config.get('CSRF_COOKIE_SECURE', False)
        self._csrf_httponly = app.config.get('CSRF_COOKIE_HTTPONLY', False)
        self._csrf_domain = app.config.get('CSRF_COOKIE_DOMAIN')
        self._type = app.config.get('SEASURF_INCLUDE_OR_EXEMPT_VIEWS',
                                    'exempt')

        return self

    def exempt(self, view):
        '''
        A decorator that can be used to exclude a view from CSRF validation.

        Example usage of :class:`exempt` might look something like this::

            csrf = SeaSurf(app)

            @csrf.exempt
            @app.route('/some_view')
            def some_view():
                return render_template('some_view.html')

        :param view: The view to be wrapped by the decorator.
        '''

        view_location = '{0}.{1}'.format(view.__module__, view.__name__)
        self._exempt_views.add(view_location)
        return view

    def exempt_urls(self, urls):
        self._exempt_urls = urls

    def include(self, view):
        '''
        A decorator that can be used to include a view from CSRF validation.

        Example usage of :class:`include` might look something like this::

            csrf = SeaSurf(app)

            @csrf.include
            @app.route('/some_view')
            def some_view():
                return render_template('some_view.html')

        :param view: The view to be wrapped by the decorator.
        '''

        view_location = '{0}.{1}'.format(view.__module__, view.__name__)
        self._include_views.add(view_location)
        return view

    def _should_use_token(self, view_func):
        '''
        Given a view function, determine whether or not we should deliver a
        CSRF token to this view through the response and validate CSRF tokens
        upon requests to this view.

        :param view_func: A view function.
        '''
        if view_func is None or self._type not in ('exempt', 'include'):
            return False

        view = '{0}.{1}'.format(view_func.__module__, view_func.__name__)
        if self._type == 'exempt' and view in self._exempt_views:
            return False

        if self._type == 'include' and view not in self._include_views:
            return False

        url = u'{0}{1}'.format(request.script_root, request.path)
        if url.startswith(self._exempt_urls):
            return False

        return True

    def _before_request(self):
        '''
        Determine if a view is exempt from CSRF validation and if not
        then ensure the validity of the CSRF token. This method is bound to
        the Flask `before_request` decorator.

        If a request is determined to be secure, i.e. using HTTPS, then we
        use strict referer checking to prevent a man-in-the-middle attack
        from being plausible.

        Validation is suspended if `TESTING` is True in your application's
        configuration.
        '''

        if self._csrf_disable:
            return  # don't validate for testing

        csrf_token = session.get(self._csrf_name, None)
        if not csrf_token:
            setattr(_app_ctx_stack.top,
                    self._csrf_name,
                    self._generate_token())
        else:
            setattr(_app_ctx_stack.top, self._csrf_name, csrf_token)

        # Always set this to let the response know whether or not to set the
        # CSRF token.
        _app_ctx_stack.top._view_func = \
            current_app.view_functions.get(request.endpoint)

        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            # Retrieve the view function based on the request endpoint and
            # then compare it to the set of exempted views
            if not self._should_use_token(_app_ctx_stack.top._view_func):
                return

            if request.is_secure:
                referer = request.headers.get('Referer')
                if referer is None:
                    error = (REASON_NO_REFERER, request.path)
                    error = u'Forbidden ({0}): {1}'.format(*error)
                    current_app.logger.warning(error)
                    return abort(403)

                # By setting the Access-Control-Allow-Origin header, browsers
                # will let you send cross-domain AJAX requests so if there is
                # an Origin header, the browser has already decided that it
                # trusts this domain otherwise it would have blocked the
                # request before it got here.
                allowed_referer = request.headers.get('Origin') or \
                                  request.url_root
                if not _same_origin(referer, allowed_referer):
                    error = REASON_BAD_REFERER.format(referer, allowed_referer)
                    error = (error, request.path)
                    error = u'Forbidden ({0}): {1}'.format(*error)
                    current_app.logger.warning(error)
                    return abort(403)

            request_csrf_token = request.form.get(self._csrf_name, '')
            if request_csrf_token == '':
                # Check to see if the data is being sent as JSON
                if hasattr(request, 'json') and request.json:
                    request_csrf_token = request.json.get(self._csrf_name, '')

            if request_csrf_token == '':
                # As per the Django middleware, this makes AJAX easier and
                # PUT and DELETE possible.
                request_csrf_token = \
                    request.headers.get(self._csrf_header_name, '')

            some_none = None in (request_csrf_token, csrf_token)
            if some_none or not safe_str_cmp(request_csrf_token, csrf_token):
                error = (REASON_BAD_TOKEN, request.path)
                error = u'Forbidden ({0}): {1}'.format(*error)
                current_app.logger.warning(error)
                return abort(403)

    def _after_request(self, response):
        '''
        Checks if the `flask._app_ctx_object` object contains the CSRF token,
        and if the view in question has CSRF protection enabled. If both,
        returns the response with a cookie containing the token. If not then we
        just return the response unaltered. Bound to the Flask `after_request`
        decorator.

        :param response: A Flask Response object.
        '''
        if getattr(_app_ctx_stack.top, self._csrf_name, None) is None:
            return response

        _view_func = getattr(_app_ctx_stack.top, '_view_func', False)
        if not (_view_func and self._should_use_token(_view_func)):
            return response

        csrf_token = getattr(_app_ctx_stack.top, self._csrf_name)
        if session.get(self._csrf_name) != csrf_token:
            session[self._csrf_name] = csrf_token
        response.set_cookie(self._csrf_name,
                            csrf_token,
                            max_age=self._csrf_timeout,
                            secure=self._csrf_secure,
                            httponly=self._csrf_httponly,
                            domain=self._csrf_domain)
        response.vary.add('Cookie')
        return response

    def _get_token(self):
        '''
        Attempts to get a token from the request cookies.
        '''
        return getattr(_app_ctx_stack.top, self._csrf_name, None)

    def _generate_token(self):
        '''
        Generates a token with randomly salted SHA1. Returns a string.
        '''
        salt = str(randrange(0, _MAX_CSRF_KEY)).encode('utf-8')
        return hashlib.sha1(salt).hexdigest()

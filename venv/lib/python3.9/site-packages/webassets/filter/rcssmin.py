from __future__ import absolute_import
from webassets.filter import Filter


__all__ = ('RCSSMin',)


class RCSSMin(Filter):
    """Minifies CSS.

    Requires the ``rcssmin`` package (https://github.com/ndparker/rcssmin).
    Alike 'cssmin' it is a port of the YUI CSS compression algorithm but aiming
    for speed instead of maximum compression.

    Supported configuration options:
    RCSSMIN_KEEP_BANG_COMMENTS (boolean)
        Keep bang-comments (comments starting with an exclamation mark).
    """

    name = 'rcssmin'
    options = {
        'keep_bang_comments': 'RCSSMIN_KEEP_BANG_COMMENTS',
    }

    def setup(self):
        super(RCSSMin, self).setup()
        try:
            import rcssmin
        except ImportError:
            raise EnvironmentError('The "rcssmin" package is not installed.')
        else:
            self.rcssmin = rcssmin

    def output(self, _in, out, **kw):
        keep = self.keep_bang_comments or False
        out.write(self.rcssmin.cssmin(_in.read(), keep_bang_comments=keep))

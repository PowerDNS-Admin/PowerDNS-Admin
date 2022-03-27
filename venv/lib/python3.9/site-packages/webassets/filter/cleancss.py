import os
from subprocess import PIPE, Popen

from webassets.filter import ExternalTool

__all__ = ('CleanCSS',)


class CleanCSS(ExternalTool):
    """
    Minify css using `Clean-css <https://github.com/GoalSmashers/clean-css/>`_.

    Clean-css is an external tool written for NodeJS; this filter assumes that
    the ``cleancss`` executable is in the path. Otherwise, you may define
    a ``CLEANCSS_BIN`` setting.

    Additional options may be passed to ``cleancss`` binary using the setting
    ``CLEANCSS_EXTRA_ARGS``, which expects a list of strings.
    """

    name = 'cleancss'
    options = {
        'binary': 'CLEANCSS_BIN',
        'extra_args': 'CLEANCSS_EXTRA_ARGS',
    }

    @property
    def cleancss_ver(self):
        if not hasattr(self, '_cleancss_ver'):
            args = [self.binary or 'cleancss']
            args += ['--version']
            # out = b"MAJOR.MINOR.REVISION" // b"3.4.19" or b"4.0.0"
            out, err = Popen(args, stdout=PIPE).communicate()
            self._cleancss_ver = int(out[:out.index(b'.')])
        return self._cleancss_ver

    def output(self, _in, out, **kw):
        args = [self.binary or 'cleancss']
        if self.extra_args:
            args.extend(self.extra_args)
        self.subprocess(args, out, _in)

    def input(self, _in, out, **kw):
        args = [self.binary or 'cleancss']
        if self.cleancss_ver < 4:
            args += ['--root', os.path.dirname(kw['source_path'])]
        if self.extra_args:
            args.extend(self.extra_args)
        self.subprocess(args, out, _in)

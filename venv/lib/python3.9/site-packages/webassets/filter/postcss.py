from __future__ import with_statement

from webassets.filter import ExternalTool
from webassets.utils import working_directory


class PostCSS(ExternalTool):
    """Processes CSS code using `PostCSS <http://postcss.org/>`_.

    Requires the ``postcss`` executable to be available externally.
    To install it, you might be able to do::

        $ npm install --global postcss

    You should also install the plugins you want to use::

        $ npm install --global postcss-cssnext

    You can configure postcss in ``postcss.config.js``:

    .. code-block:: javascript

        module.exports = {
            plugins: [
                require('postcss-cssnext')({
                  // optional configuration for cssnext
                })
            ],
        };

    *Supported configuration options*:

    POSTCSS_BIN
        Path to the postcss executable used to compile source files. By
        default, the filter will attempt to run ``postcss`` via the
        system path.

    POSTCSS_EXTRA_ARGS
        Additional command-line options to be passed to ``postcss`` using this
        setting, which expects a list of strings.

    """
    name = 'postcss'

    options = {
        'binary': 'POSTCSS_BIN',
        'extra_args': 'POSTCSS_EXTRA_ARGS',
    }

    max_debug_level = None

    def input(self, in_, out, source_path, **kw):
        # Set working directory to the source file so that includes are found
        args = [self.binary or 'postcss']
        if self.extra_args:
            args.extend(self.extra_args)
        with working_directory(filename=source_path):
            self.subprocess(args, out, in_)

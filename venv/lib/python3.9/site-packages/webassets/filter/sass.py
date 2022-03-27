from __future__ import print_function

import os

from webassets.filter import ExternalTool

__all__ = ('Sass', 'SCSS')


class Sass(ExternalTool):
    """Converts `Sass <http://sass-lang.com/>`_ markup to
    real CSS.

    Requires the Sass executable to be available externally. To install
    it, you might be able to do::

         $ sudo npm install -g sass

    By default, this works as an "input filter", meaning ``sass`` is
    called for each source file in the bundle. This is because the
    path of the source file is required so that @import directives
    within the Sass file can be correctly resolved.

    However, it is possible to use this filter as an "output filter",
    meaning the source files will first be concatenated, and then the
    Sass filter is applied in one go. This can provide a speedup for
    bigger projects.

    To use Sass as an output filter::

        from webassets.filter import get_filter
        sass = get_filter('sass', as_output=True)
        Bundle(...., filters=(sass,))

    However, if you want to use the output filter mode and still also
    use the @import directive in your Sass files, you will need to
    pass along the ``load_paths`` argument, which specifies the path
    to which the imports are relative to (this is implemented by
    changing the working directory before calling the ``sass``
    executable)::

        sass = get_filter('sass', as_output=True, load_paths='/tmp')

    With ``as_output=True``, the resulting concatenation of the Sass
    files is piped to Sass via stdin (``cat ... | sass --stdin ...``)
    and may cause applications to not compile if import statements are
    given as relative paths.

    For example, if a file ``foo/bar/baz.scss`` imports file
    ``foo/bar/bat.scss`` (same directory) and the import is defined as
    ``@import "bat";`` then Sass will fail compiling because Sass
    has naturally no information on where ``baz.scss`` is located on
    disk (since the data was passed via stdin) in order for Sass to
    resolve the location of ``bat.scss``::

        Traceback (most recent call last):
        ...
        webassets.exceptions.FilterError: sass: subprocess had error: stderr=(sass):1: File to import not found or unreadable: bat. (Sass::SyntaxError)
               Load paths:
                 /path/to/project-foo
                on line 1 of standard input
          Use --trace for backtrace.
        , stdout=, returncode=65

    To overcome this issue, the full path must be provided in the
    import statement, ``@import "foo/bar/bat"``, then webassets
    will pass the ``load_paths`` argument (e.g.,
    ``/path/to/project-foo``) to Sass via its ``-I`` flags so Sass can
    resolve the full path to the file to be imported:
    ``/path/to/project-foo/foo/bar/bat``

    Support configuration options:

    SASS_BIN
        The path to the Sass binary. If not set, the filter will
        try to run ``sass`` as if it's in the system path.

    SASS_STYLE
        The style for the output CSS. Can be one of ``expanded`` (default)
        or ``compressed``.

    SASS_AS_OUTPUT
        By default, this works as an "input filter", meaning ``sass`` is
        called for each source file in the bundle. This is because the
        path of the source file is required so that @import directives
        within the Sass file can be correctly resolved.

        However, it is possible to use this filter as an "output filter",
        meaning the source files will first be concatenated, and then the
        Sass filter is applied in one go. This can provide a speedup for
        bigger projects.

        It will also allow you to share variables between files.

    SASS_LOAD_PATHS
        It should be a list of paths relatives to Environment.directory or absolute paths.
        Order matters as sass will pick the first file found in path order.
        These are fed into the -I flag of the sass command and
        is used to control where sass imports code from.
    """
    # TODO: If an output filter could be passed the list of all input
    # files, the filter might be able to do something interesting with
    # it (for example, determine that all source files are in the same
    # directory).

    name = 'sass'
    options = {
        'binary': 'SASS_BIN',
        'use_scss': ('scss', 'SASS_USE_SCSS'),
        'as_output': 'SASS_AS_OUTPUT',
        'load_paths': 'SASS_LOAD_PATHS',
        'style': 'SASS_STYLE',
    }
    max_debug_level = None

    def resolve_path(self, path):
        return self.ctx.resolver.resolve_source(self.ctx, path)

    def _apply_sass(self, _in, out, cd=None):
        # Switch to source file directory if asked, so that this directory
        # is by default on the load path. We could pass it via -I, but then
        # files in the (undefined) wd could shadow the correct files.
        orig_cwd = os.getcwd()
        child_cwd = orig_cwd
        if cd:
            child_cwd = cd

        args = [self.binary or 'sass',
                '--stdin',
                '--style', self.style or 'expanded']

        if not self.use_scss:
            args.append("--indented")

        for path in self.load_paths or []:
            if os.path.isabs(path):
                abs_path = path
            else:
                abs_path = self.resolve_path(path)
            args.extend(['-I', abs_path])

        return self.subprocess(args, out, _in, cwd=child_cwd)

    def input(self, _in, out, source_path, output_path, **kw):
        if self.as_output:
            out.write(_in.read())
        else:
            self._apply_sass(_in, out, os.path.dirname(source_path))

    def output(self, _in, out, **kwargs):
        if not self.as_output:
            out.write(_in.read())
        else:
            self._apply_sass(_in, out)


class SCSS(Sass):
    """Version of the ``sass`` filter that uses the SCSS syntax.
    """

    name = 'scss'

    def __init__(self, *a, **kw):
        assert 'scss' not in kw
        kw['scss'] = True
        super(SCSS, self).__init__(*a, **kw)

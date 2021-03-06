# -*- coding: utf-8 -*-
"""magics for using blockdiag.com modules with IPython Notebook

The module provides magics:  %%actdiag, %%blockdiag, %%nwdiag, %%seqdiag

Sample usage (in IPython cell):

    %%blockdiag
    {
       A -> B -> C;
            B -> D;
    }

Some browsers do not properly render SVG, therefore PNG image is used by default.

Use magics %setdiagsvg and %setdiagpng to set SVG or PNG mode

PNG rendered on windows with default libraries does not support antialiasing,
resulting in a poor image quality

If inkscape is installed on the machine and can be found in system path,
the diagram is created as SVG and then rendered to PNG using inkscape.

Inkscape for windows can be downloaded from (http://inkscape.org/)

"""
from __future__ import print_function

import imp
import io
import os
import sys
import pipes
import subprocess
import tempfile

try:
    import hashlib
except ImportError:
    import md5 as hashlib

from IPython.core.magic import Magics, magics_class, cell_magic, line_cell_magic
from IPython.core.displaypub import publish_display_data

_draw_mode = 'PNG'
_publish_mode = 'PNG'

_inkscape_available = None

@magics_class
class BlockdiagMagics(Magics):
    """Magics for blockdiag and others"""

    def _import_all(self, module):
        for k, v in module.__dict__.items():
            if not k.startswith('__'):
                self.shell.push({k:v})

    def run_command(self, args):
        try:
            startupinfo = None
            if os.name == 'nt':
                # Avoid a console window in Microsoft Windows.
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.call(args, stderr=subprocess.STDOUT,
                                  startupinfo=startupinfo)
            return True
        except subprocess.CalledProcessError as e:
            print(e.output, file=sys.stderr)
            print("ERROR: command `%s` failed\n%s" %
                      ' '.join(map(pipes.quote, e.cmd)),
                      file=sys.stderr)
        except OSError as e:
            import traceback
            print ('Exception %s' % str(e), file=sys.stdout)
        return False

    def inkscape_available(self):
        global _inkscape_available
        if _inkscape_available is None:
            _inkscape_available = self.run_command(['inkscape', '--export-png'])
        return _inkscape_available

    def svg2png(self, filename):
        self.run_command(['inkscape', filename + '.svg',
                '--export-png=' + filename + '.png'])

    def diag(self, line, cell, command):
        """Create sequence diagram using supplied diag methods."""
        code = cell + u'\n'
        # if inkscape is available create SVG for either case
        if self.inkscape_available():
            global _draw_mode
            _draw_mode = 'SVG'

        try:
            tmpdir = tempfile.mkdtemp()
            fd, diag_name = tempfile.mkstemp(dir=tmpdir)
            f = os.fdopen(fd, "wb")
            f.write(code.encode('utf-8'))
            f.close()

            format = _draw_mode.lower()
            draw_name = diag_name + '.' + format

            saved_argv = sys.argv
            argv = [diag_name, '-T', format, '-o', draw_name]

            # if os.path.exists(fontpath):
            #    sys.argv += ['-f', fontpath]

            # do not use PIL library when rendering to SVG
            # this allows avoid problem with handling unicode in diagram
            if _draw_mode == 'SVG':
                argv += ['']

            # Run command
            command.main(argv)

            if _draw_mode == 'SVG' and _publish_mode == 'PNG':
                # render SVG with inkscape
                self.svg2png(diag_name)

            file_name = diag_name + '.' + _publish_mode.lower()
            with io.open(file_name, 'rb') as f:
                data = f.read()
                f.close()

        finally:
            for file in os.listdir(tmpdir):
                os.unlink(tmpdir + "/" + file)
            os.rmdir(tmpdir)

        if _publish_mode == 'SVG':
            publish_display_data(
                u'IPython.core.displaypub.publish_svg',
                None,
                {'image/svg+xml':data}
            )
        else:
            publish_display_data(
                {'image/png':data},
                None,
                u'IPython.core.displaypub.publish_png',
            )

    @cell_magic
    def actdiag(self, line, cell):
        import actdiag.command
        self.diag(line, cell, actdiag.command)

    @cell_magic
    def blockdiag(self, line, cell):
        import blockdiag.command
        self.diag(line, cell, blockdiag.command)

    @cell_magic
    def nwdiag(self, line, cell):
        import nwdiag.command
        self.diag(line, cell, nwdiag.command)

    @cell_magic
    def seqdiag(self, line, cell):
        import seqdiag.command
        self.diag(line, cell, seqdiag.command)

    @line_cell_magic
    def setdiagsvg(self, line, cell=None):
        global _draw_mode, _publish_mode
        _draw_mode = _publish_mode = 'SVG'

    @line_cell_magic
    def setdiagpng(self, line, cell=None):
        global _draw_mode, _publish_mode
        _draw_mode = _publish_mode = 'PNG'


_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(BlockdiagMagics)
        _loaded = True


if __name__ == '__main__':
    #
    # for testing only
    #
    cell = u""" {
        A -> B -> C;
        B -> D;
        }
    """
    bm = BlockdiagMagics('test')
    bm.seqdiag('', cell)

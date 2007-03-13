
import subprocess

import gtk

from kiwi.ui.objectlist import ObjectList, Column, ColoredColumn

p = subprocess.Popen(['nosetests', '--with-coverage', '--cover-package=pida'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)

class Line(object):

    def __init__(self, vals):
        self.name = vals[0]
        self.percentage = int(vals[3].rstrip('%'))
        self.missing = ' '.join(vals[4:])

class Reader(object):

    def __init__(self, p):
        self._p  = p
        self._on = False
        self._lines = []

        for line in self._p.stderr:
            if self._on:
                vals = line.strip().split()
                if len(vals) >= 3:
                    if '%' in vals[3]:
                        self._lines.append(Line(vals))
                
            if line.startswith('---'):
                self._on = not self._on


    def build_tree(self):
        w = gtk.Window()
        w.connect('delete-event', lambda *a: gtk.main_quit())
        ol = ObjectList(
            [
                Column('name'),
                ColoredColumn('percentage', data_type=int, sorted=True,
                    color='red', data_func = lambda i: i < 100),
                Column('missing')
            ],
            sortable = True
        )
        self._lines.sort(lambda x, y: x.percentage - y.percentage)
        for line in self._lines:
            ol.append(line)
        w.set_title('PIDA Tests Coverage')
        w.resize(600, 900)
        w.add(ol)
        w.show_all()
        gtk.main()

if __name__ == '__main__':
    Reader(p).build_tree()

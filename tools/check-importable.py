import py.path

pida_root = py.path.local(__file__).dirpath().dirpath()
subdirs = 'pida pida-plugins tests'.split()

for subdir in subdirs:
    path = pida_root/subdir

    for pyfile in path.visit('*.py'):
        try:
            pyfile.pyimport()
        except:
            print pyfile, 'not importable'

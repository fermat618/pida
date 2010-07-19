# -*- coding: utf-8 -*- 
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""


import subprocess

from pygtkhelpers.gthreads import GeneratorTask

class GeneratorSubprocessTask(GeneratorTask):
    """
    A Generator Task for launching a subprocess

    An example (inside thread_inited gtk main loop):
        def output(line):
            print line
        task = GeneratorSubprocessTask(output)
        task.start(['ls', '-al'])
    """
    def __init__(self, stdout_callback, complete_callback=None):
        GeneratorTask.__init__(self, self.start_process, stdout_callback,
                               complete_callback)

    def start_process(self, commandargs, **spargs):
        self._process = subprocess.Popen(
            commandargs,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
            **spargs
        )
        for line in self._process.stdout:
            yield line.strip()

    def stop(self):
        GeneratorTask.stop(self)
        try:
            if hasattr(self, '_process'):
                self._process.kill()
        except OSError:
            pass



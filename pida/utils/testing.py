""" Some things to make testing the UI a bit nicer """
import time

import gtk

def refresh_gui(delay=0):
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
    time.sleep(delay)


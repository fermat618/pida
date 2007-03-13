""" Some things to make testing the UI a bit nicer """


# stlib
import time

# gtk
import gtk

# Stolen from Kiwi
def refresh_gui(delay=0):
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
    time.sleep(delay)




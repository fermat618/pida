
from urllib import urlopen, urlencode

from pida.utils.gthreads import AsyncTask

def fetch_url(url, content_callback, data={}):
    """Asynchronously fetch a URL"""
    if data:
        urlargs = (url, urlencode(data))
    else:
        urlargs = (url,)

    def _fetcher():
        try:
            f = urlopen(*urlargs)
            content = f.read()
            url = f.url
        except Exception, e:
            content = str(e)
            url = None
        print content, url
        return url, content

    task = AsyncTask(_fetcher, content_callback) 
    task.start()

if __name__ == '__main__':
    
    def cc(url, data):
        print url, data
        gtk.main_quit()

    fetch_url('http://google.com/sdfsdfsdf', cc)
    import gtk
    gtk.threads_init()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()


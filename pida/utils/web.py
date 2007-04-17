
from urllib import urlopen, urlencode

from pida.utils.gthreads import AsyncTask

def fetch_url(self, url, content_callback, data={}):
    """Asynchronously fetch a URL"""
    def _fetcher():
        try:
            data = urlopen(url).read()
        except Exception, e:
            data = str(e)
        return data

    task = AsyncTask(_fetcher, content_callback) 
    task.start()


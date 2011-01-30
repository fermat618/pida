from .notify import NotifyItem



def test_can_pass_non_str():
    NotifyItem(title=object, data=object, stock=None, timeout=0, callback=None)

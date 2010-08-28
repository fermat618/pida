# -*- coding: utf-8 -*-
from mock import Mock
from execnet.gateway_base import Channel
from pygtkhelpers.ui.objectlist import ObjectList

from .nosetest import NoseTester


def test_data_mapper():

    channel = Mock(Channel)
    view = Mock(ObjectList)

    tester = NoseTester(view, channel)

    assert channel.setcallback.called

    tester.callback('start_ctx', 'foo.bar', 'test.py')
    assert view.append.called








# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

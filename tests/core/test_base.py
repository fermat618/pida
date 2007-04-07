from unittest import TestCase

from pida.core.base import BaseConfig

from pida.utils.testing.mock import Mock

class TestConfig(BaseConfig):

    """A Test Subclass"""

class BaseConfigTest(TestCase):

    def setUp(self):
        self._svc = Mock({'get_name': 'banana'})
        self._conf = TestConfig(self._svc)

    def test_get_name(self):
        self.assertEqual(self._conf.get_service_name(), 'banana')
    

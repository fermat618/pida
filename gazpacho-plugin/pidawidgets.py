

from pida2.ui.views import PidaServiceView
from gazpacho.loader.custom import Adapter, ComboBoxAdapter, \
     PythonWidgetAdapter, adapter_registry
from gazpacho.widgets.base.base import ContainerAdaptor
from gazpacho.widgetregistry import widget_registry



class PidaServiceViewAdapter(ContainerAdaptor):
    widget_type = PidaServiceView
    """Pass"""

adapter_registry.register_adapter(PidaServiceViewAdapter)

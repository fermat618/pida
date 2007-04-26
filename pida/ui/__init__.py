
import icons

from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.ui.objectlist import ObjectList, ObjectTree


### Monkey Patching

from pida.ui.objectlist import sort_by_attribute

if not hasattr(ObjectList, 'sort_by_attribute'):
    ObjectList.sort_by_attribute = sort_by_attribute

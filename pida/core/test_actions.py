
import pida.core.actions as actions
import unittest
import gtk
#from pida.core.testing import test, assert_equal

class Something:
    NAME="foo"

class MyHandler(actions.action_handler):
    def act_normal_action_1(self, action):
        pass
    
    def act_normal_action_2(self, action):
        """I have a tooltip"""

    def act_find_something(self, action):
        """Tooltip and gtk.STOCK_FIND"""
    
    @actions.action(name="another_name")
    def act_some_name(self, action):
        pass

    @actions.action(type=actions.TYPE_NORMAL)
    def act_normal_action_3(self, action):
        pass

    @actions.action(label="Label", is_important=True, type=actions.TYPE_TOGGLE)
    def act_normal_action_4(self, action):
        pass

    @actions.action(type=actions.TYPE_RADIO, value=0)
    def act_radio1(self, action):
        pass

    @actions.action(type=actions.TYPE_RADIO, value=1, group="radio1")
    def act_radio2(self, action):
        pass

    @actions.action(type=actions.TYPE_RADIO, value=0, name="Something")
    def act_radio3(self, action):
        pass

    @actions.action(type=actions.TYPE_RADIO, value=1, group="Something")
    def act_radio4(self, action):
        pass


def c():
    handler = MyHandler(Something())
    actions = handler.action_group
    return handler, actions

def get_action(actions, name):
    return actions.get_action("foo+action-handler+%s" % name)



class ActionTest(unittest.TestCase):


    def checkAction(self, actions, name="", tooltip=None, stock_id="",
        action_type=actions.PidaAction, action=None, is_important=False, label=""):
        if action is None:
            action = get_action(actions, name)
        assert action is not None
        self.assertEqual(type(action), action_type)
        self.assertEqual(tooltip, action.get_property("tooltip"))
        self.assertEqual(stock_id, action.get_property("stock-id"))
        self.assertEqual(is_important, action.get_property("is-important"))
        self.assertEqual(label, action.get_property("label"))

    def test_actions(self):
        handler, actions = c()
        self.assertEqual(10, len(actions.list_actions()))
    

    def test_action1(self):
        handler, actions = c()
        self.checkAction(
            actions,
            name = "normal_action_1",
            tooltip = None,
            stock_id = "gtk-normal",
            label = "Normal Action 1",
        )

    def test_action2(self):
        handler, actions = c()
        self.checkAction(
            actions,
            name = "normal_action_2",
            tooltip = "I have a tooltip",
            stock_id = "gtk-normal",
            label = "Normal Action 2",
        )

    def test_action3(self):
        handler, actions = c()
        self.checkAction(
            actions,
            name = "find_something",
            tooltip = "Tooltip and gtk.STOCK_FIND",
            stock_id = gtk.STOCK_FIND,
            label = "Find Something",
        )

    def test_action4(self):
        handler, actions = c()
        self.checkAction(
            actions,
            action = actions.get_action("another_name"),
            tooltip = None,
            stock_id = "gtk-another",
            label = "Another Name",
        )

    def test_action5(self):
        handler, actions = c()
        self.checkAction(
            actions,
            name = "normal_action_3",
            tooltip = None,
            stock_id = "gtk-normal",
            label = "Normal Action 3",
        )

    def test_action6(self):
        handler, acts = c()
        self.checkAction(
            acts,
            name = "normal_action_4",
            tooltip = None,
            stock_id = "gtk-normal",
            label = "Label",
            is_important = True,
            action_type = actions.PidaToggleAction,
        )

    def test_action7(self):
        handler, acts = c()
        self.checkAction(
            acts,
            name = "radio1",
            tooltip = None,
            stock_id = "gtk-radio1",
            label = "Radio1",
            action_type = actions.PidaRadioAction
        )
        act = get_action(acts, "radio1")
        self.assertEqual(0, act.get_property("value"))
        self.assertEqual(2, len(act.get_group()))
        assert act in act.get_group()

    def test_action8(self):
        handler, acts = c()
        self.checkAction(
            acts,
            name = "radio2",
            tooltip = None,
            stock_id = "gtk-radio2",
            label = "Radio2",
            action_type = actions.PidaRadioAction
        )
        act = get_action(acts, "radio2")
        self.assertEqual(1, act.get_property("value"))
        self.assertEqual(2, len(act.get_group()))
        assert act in act.get_group()

    def test_action9(self):
        handler, acts = c()
        self.checkAction(
            acts,
            action = acts.get_action("Something"),
            tooltip = None,
            stock_id = "gtk-something",
            label = "Something",
            action_type = actions.PidaRadioAction
        )
        act = acts.get_action("Something")
        self.assertEqual(0, act.get_property("value"))
        self.assertEqual(2, len(act.get_group()))
        assert act in act.get_group()

    def test_action10(self):
        handler, acts = c()
        self.checkAction(
            acts,
            name = "radio4",
            tooltip = None,
            stock_id = "gtk-radio4",
            label = "Radio4",
            action_type = actions.PidaRadioAction
        )
        act = get_action(acts, "radio4")
        self.assertEqual(1, act.get_property("value"))
        self.assertEqual(2, len(act.get_group()))
        assert act in act.get_group()


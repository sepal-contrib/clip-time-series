import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from traitlets import observe


class IdSelect(sw.SepalWidget, v.Select):

    ALL = "all"

    def __init__(self):

        # create the widget
        super().__init__(
            items=[self.ALL],
            label="Select Points",
            v_model=[self.ALL],
            multiple=True,
            chips=True,
            deletable_chips=True,
        )

    @observe("v_model")
    def _check_value(self, change):
        """if "all" is selected, all other values should be removed and respectively."""
        # monkey patch to avoid bug at runtile
        change["new"] = change["new"] or []
        change["old"] = change["old"] or []

        # exit if its a removal
        if len(change["new"]) <= len(change["old"]):
            return self

        # guess the new input
        new_value = list(set(change["new"]) - set(change["old"]))[0]

        if new_value == self.ALL:
            self.v_model = [self.ALL]
        else:
            tmp_v = self.v_model.copy()
            if self.ALL in tmp_v:
                tmp_v.remove(self.ALL)
            self.v_model = tmp_v

        return self

    def set_items(self, items):
        """add items + the "all" value."""
        # clean the selection
        self.v_model = [self.ALL]

        # set the items
        self.items = [self.ALL, {"divider": True}, *items]

        return self

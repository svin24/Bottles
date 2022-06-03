# envvars.py
#
# Copyright 2020 brombinmirko <send@mirko.pm>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from gi.repository import Gtk, GLib, Adw


@Gtk.Template(resource_path='/com/usebottles/bottles/env-var-entry.ui')
class EnvVarEntry(Adw.EntryRow):
    __gtype_name__ = 'EnvVarEntry'

    # region Widgets
    btn_remove = Gtk.Template.Child()
    ev_controller = Gtk.EventControllerKey.new()
    # endregion

    def __init__(self, parent, env, **kwargs):
        super().__init__(**kwargs)

        # common variables and references
        self.parent = parent
        self.manager = parent.window.manager
        self.config = parent.config
        self.env = env

        self.set_title(self.env[0])
        self.set_text(self.env[1])

        self.add_controller(self.ev_controller)

        # connect signals
        self.ev_controller.connect("key-pressed", self.on_change)
        self.connect("apply", self.__save)
        self.btn_remove.connect("clicked", self.__remove)

    def on_change(self, *args):
        self.set_show_apply_button(self.get_text() != "")

    def __save(self, *args):
        """
        Change the env var value according to the
        user input and update the bottle configuration
        """
        self.manager.update_config(
            config=self.config,
            key=self.env[0],
            value=self.get_text(),
            scope="Environment_Variables"
        )

    def __remove(self, *args):
        """
        Remove the env var from the bottle configuration and
        destroy the widget
        """
        self.manager.update_config(
            config=self.config,
            key=self.env[0],
            value=False,
            remove=True,
            scope="Environment_Variables"
        )
        self.parent.list_vars.remove(self)


@Gtk.Template(resource_path='/com/usebottles/bottles/dialog-env-vars.ui')
class EnvVarsDialog(Adw.Window):
    __gtype_name__ = 'EnvVarsDialog'

    # region Widgets
    entry_name = Gtk.Template.Child()
    list_vars = Gtk.Template.Child()
    ev_controller = Gtk.EventControllerKey.new()
    # endregion

    def __init__(self, window, config, **kwargs):
        super().__init__(**kwargs)
        self.set_transient_for(window)

        # common variables and references
        self.window = window
        self.manager = window.manager
        self.config = config

        self.__populate_vars_list()
        self.entry_name.add_controller(self.ev_controller)

        # connect signals
        self.ev_controller.connect("key-pressed", self.__validate)
        self.entry_name.connect("apply", self.__save_var)

    def __validate(self, *args):
        regex = re.compile('[@!#$%^&*()<>?/|}{~:.;,\'"]')
        name = self.entry_name.get_text()
        res = (regex.search(name) is None) and name != ""
        self.entry_name.set_show_apply_button(res)

    def __save_var(self, *args):
        """
        This function save the new env var to the
        bottle configuration
        """
        env_name = self.entry_name.get_text()
        self.manager.update_config(
            config=self.config,
            key=env_name,
            value="",
            scope="Environment_Variables"
        )
        _entry = EnvVarEntry(parent=self, env=[env_name, ""])
        GLib.idle_add(self.list_vars.add, _entry)
        self.entry_name.set_text("")
        self.entry_name.set_show_apply_button(False)

    def __populate_vars_list(self):
        """
        This function populate the list of env vars
        with the existing ones from the bottle configuration
        """
        envs = self.config.get("Environment_Variables").items()
        if len(envs) == 0:
            self.list_vars.set_description(_("No environment variables defined"))
            return

        self.list_vars.set_description("")
        for env in envs:
            _entry = EnvVarEntry(parent=self, env=env)
            GLib.idle_add(self.list_vars.add, _entry)

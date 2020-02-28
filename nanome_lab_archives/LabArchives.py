import os
import shutil
import tempfile
import time

import nanome
from nanome.util import Logs
# there we go. change other places
# .LAClient is folder, LAClient(.py) is module, containing class LAClient
from .IOManager import IOManager
from .LAClient import LAClient
from .menus.LoginSignup import LoginSignup
from .menus.NotebooksMenu import NotebooksMenu
from .menus.FileMenu import FileMenu
from .NotebookFolderFile import Notebook

class LabArchives(nanome.PluginInstance):
    def start(self):
        self.__client = LAClient.LAClient("https://api.labarchives.com/api", os.path.join(os.getcwd(), '..', 'Authentication', 'plugin-lab-archives', 'credentials.txt'))

        self.__menu_login = LoginSignup(self)
        self.__menu_login.register_login_callback(self.open_notebooks)
        self.__menu_login.register_signup_callback(self.handle_signup)
        self.__menu_login.open_menu()

        self.__menu_notebooks = NotebooksMenu(self)
        self.__menu_file = FileMenu(self)

    def open_notebooks(self, err, res):
        if err is None: #
            notebooks = Notebook.parse(res['users']['notebooks'])
            self.__menu_notebooks.open_menu(notebooks)

            LAClient.Tree.get_tree_level(notebooks[0].nbid, 0)
        else:
            pass

    def open_file(self, file, button=None):
        self.__menu_file.open_menu(file)

    def handle_signup(self, err, res):
        if err is None or len('redundant account case') > 0:
            self.__menu_login.switch_to_login()
        else:
            print(err)

    def reopen_menu(self, menu):
        menu.enabled = True

    def on_stop(self):
        IOManager.cleanup()

def main():
    plugin = nanome.Plugin('LabArchives', 'Interact with LabArchives notebooks from within Nanome', 'Utilities', False)
    plugin.set_plugin_class(LabArchives)
    plugin.run('127.0.0.1', 8888)

if __name__ == '__main__':
    main()
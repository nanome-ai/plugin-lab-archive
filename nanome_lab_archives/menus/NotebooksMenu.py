import os
import time
import tempfile
from functools import partial

import nanome

from ..IOManager import IOManager
from ..NotebookFolderFile import Notebook, Folder, File
from ..LAClient import LAClient

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
BASEPATH = os.path.normpath(os.path.join(DIR_PATH, '..'))

NOTEBOOKS_MENU_PATH = os.path.join(DIR_PATH, 'json', 'notebooks.json')

NOTEBOOK_ICON = os.path.join(BASEPATH, 'images', 'notebook.png')
print(BASEPATH)
FOLDER_ICON = os.path.join(BASEPATH, 'images', 'folder.png')
FILE_ICON = os.path.join(BASEPATH, 'images', 'file.png')

PDBOPTIONS = nanome.api.structure.Complex.io.PDBSaveOptions()
PDBOPTIONS.write_bonds = False

class NotebooksMenu():
    def __init__(self, plugin, closed_callback=None):
        self.__plugin = plugin
        self.__menu = nanome.ui.Menu.io.from_json(NOTEBOOKS_MENU_PATH)
        self.__menu.register_closed_callback(closed_callback if closed_callback is not None else self.reopen_menu)

        self.__default_nbid = None

        self.__btn_upload = self.__menu.root.find_node('Upload First').get_content()
        self.__btn_upload.register_pressed_callback(self.upload_first)
        self.__btn_download = self.__menu.root.find_node('Download First').get_content()
        self.__btn_download.register_pressed_callback(self.download_first)
        self.__download_eid = None

        self.__ln_notebooks = self.__menu.root.find_node('Notebooks')

        self.__prefab_node = self.__menu.root.find_node('Node')

    def open_menu(self, notebooks=None):
        if notebooks is not None:
            self.display_notebooks(notebooks)

        self.__menu.unusable = True
        self.__plugin.menu = self.__menu
        self.__plugin.update_menu(self.__menu)

    def reopen_menu(self, menu):
        self.__menu.unusable = True
        self.__plugin.update_menu(self.__menu)

    def get_ui_list_index(self, item):
        items = self.__ln_notebooks.get_content().items
        for i, some_item in enumerate(items):
            if some_item is item:
                return i

        return len(items)

    def create_node(self, entry, where):
        node_clone = self.__prefab_node.clone()
        button = node_clone.find_node('Button').get_content()
        icon = node_clone.find_node('Icon')
        name_content = node_clone.find_node('Name').get_content()
        name_content.text_value = entry.name

        if isinstance(entry, Notebook):
            icon.add_new_image(NOTEBOOK_ICON)
        elif isinstance(entry, Folder):
            icon.add_new_image(FOLDER_ICON)
        elif isinstance(entry, File):
            icon.add_new_image(FILE_ICON)
            open_file = partial(self.__plugin.open_file, entry)
            button.register_pressed_callback(open_file)

        index = self.get_ui_list_index(where)
        self.__ln_notebooks.get_content().items.insert(index, node_clone)

    def display_notebooks(self, notebooks):
        for notebook in notebooks:
            self.create_node(notebook, None)
            self.__default_nbid = self.__default_nbid or notebook.nbid
            (err, res) = LAClient.Tree.get_tree_level(notebook.nbid, 0)
            Notebook.update_notebook(notebook, res, notebook)
            for item in notebook.items:
                self.create_node(item, None)

    def upload_first(self, button):
        def write_and_upload(complexes):
            # write
            file = IOManager.get_file(complex.name)
            complex = complexes[0]
            complex.io.to_pdb(file.name, PDBOPTIONS)
            print("pdb location:", file.name)
            # upload
            err = 'while init'
            while err is not None:
                with open(file.name, 'rb') as pdbfilecontent:
                    pid = ''
                    (err, res) = LAClient.Entries.add_attachment(
                        f'{complex.full_name.strip(" {}")}.pdb',
                        "Uploaded by nanome-lab-archives plugin",
                        self.__default_nbid,
                        'MS4zfDU0NTE4NS8xL1RyZWVOb2RlLzI1NjcxNDMyNDl8My4z',
                        pdbfilecontent)
                time.sleep(3)
            self.__btn_upload.unusable = False
            self.__plugin.update_menu(self.__menu)
            print("SUCCESSFULLY UPLOADED.")
            # notify
            self.__plugin.send_notification(nanome.util.enums.NotificationTypes.success, f"Uploaded {complex.name} to LabArchives")
            self.__download_eid = res['entries']['entry']['eid']

        def received_complex_list(complex_list):
            index = complex_list[0].index
            self.__plugin.request_complexes([index], write_and_upload)
        self.__btn_upload.unusable = True
        self.__plugin.update_menu(self.__menu)
        self.__plugin.request_complex_list(received_complex_list)

    def download_first(self, button):
        file = IOManager.get_file('1TYL.pdb')
        self.__btn_download.unusable = True
        self.__plugin.update_menu(self.__menu)
        if self.__download_eid is None:
            self.__plugin.send_notification(nanome.util.enums.NotificationTypes.error, "No structures uploaded yet")
            return

        err = 'while init'
        while err is not None:
            (err, res) = LAClient.Entries.entry_attachment(self.__download_eid, file.name)
            if res is not None: print("Received valid response...")
            time.sleep(3)
        self.__plugin.update_menu(self.__menu)

        complex = nanome.structure.Complex.io.from_pdb(path=file.name)
        def upload(complexes):
            print("Uploading to nanome...")
            self.__plugin.add_to_workspace(complexes)
            self.__btn_download.unusable = False
            print("SUCCESSFULLY DOWNLOADED.")
            self.__plugin.send_notification(nanome.util.enums.NotificationTypes.success, "Successfully imported from LabArchive")
        self.__plugin.add_bonds([complex], upload, True)
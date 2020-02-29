import os
import time
import tempfile
from functools import partial

import nanome

from ..IOManager import IOManager
from ..NotebookFolderFile import Notebook, Folder, File
from ..LAClient import LAClient, Tree, Entries

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
        self.plugin = plugin
        self.menu = nanome.ui.Menu.io.from_json(NOTEBOOKS_MENU_PATH)
        self.menu.register_closed_callback(closed_callback if closed_callback is not None else self.reopen_menu)

        self.default_nbid = None

        self.btn_upload = self.menu.root.find_node('Upload First').get_content()
        self.btn_upload.register_pressed_callback(self.upload_first)
        self.btn_download = self.menu.root.find_node('Download First').get_content()
        self.btn_download.register_pressed_callback(self.download_first)
        self.download_eid = None

        self.ln_notebooks = self.menu.root.find_node('Notebooks')

        self.pfb_node = self.menu.root.find_node('Node')

    def open_menu(self, notebooks=None):
        if notebooks is not None:
            self.display_notebooks(notebooks)

        self.menu.unusable = True
        self.plugin.menu = self.menu
        self.plugin.update_menu(self.menu)

    def reopen_menu(self, menu):
        self.menu.unusable = True
        self.plugin.update_menu(self.menu)

    def get_ui_list_index(self, item):
        items = self.ln_notebooks.get_content().items
        for i, some_item in enumerate(items):
            if some_item is item:
                return i

        return len(items)

    def create_node(self, entry, where):
        node_clone = self.pfb_node.clone()
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
            open_file = partial(self.plugin.open_file, entry)
            button.register_pressed_callback(open_file)

        index = self.get_ui_list_index(where)
        if where:
            node_clone.set_padding(left=(where.nesting+1)*0.13)
        self.ln_notebooks.get_content().items.insert(index, node_clone)

    def display_notebooks(self, notebooks):
        for notebook in notebooks:
            notebook.nesting = 0
            self.create_node(notebook, None)
            self.default_nbid = self.default_nbid or notebook.nbid
            (err, res) = Tree.get_tree_level(notebook.nbid, 0)
            Notebook.update_notebook(notebook, res, notebook)
            for item in notebook.items:
                self.create_node(item, notebook)

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
                    (err, res) = Entries.add_attachment(
                        f'{complex.full_name.strip(" {}")}.pdb',
                        "Uploaded by nanome-lab-archives plugin",
                        self.default_nbid,
                        'MS4zfDU0NTE4NS8xL1RyZWVOb2RlLzI1NjcxNDMyNDl8My4z',
                        pdbfilecontent)
                time.sleep(3)
            self.btn_upload.unusable = False
            self.plugin.update_menu(self.menu)
            print("SUCCESSFULLY UPLOADED.")
            # notify
            self.plugin.send_notification(nanome.util.enums.NotificationTypes.success, f"Uploaded {complex.name} to LabArchives")
            self.download_eid = res['entries']['entry']['eid']

        def received_complex_list(complex_list):
            index = complex_list[0].index
            self.plugin.request_complexes([index], write_and_upload)
        self.btn_upload.unusable = True
        self.plugin.update_menu(self.menu)
        self.plugin.request_complex_list(received_complex_list)

    def download_first(self, button):
        file = IOManager.get_file('1TYL.pdb')
        self.btn_download.unusable = True
        self.plugin.update_menu(self.menu)
        if self.download_eid is None:
            self.plugin.send_notification(nanome.util.enums.NotificationTypes.error, "No structures uploaded yet")
            return

        err = 'while init'
        while err is not None:
            (err, res) = Entries.entry_attachment(self.download_eid, file.name)
            if res is not None: print("Received valid response...")
            time.sleep(3)
        self.plugin.update_menu(self.menu)

        complex = nanome.structure.Complex.io.from_pdb(path=file.name)
        def upload(complexes):
            print("Uploading to nanome...")
            self.plugin.add_to_workspace(complexes)
            self.btn_download.unusable = False
            print("SUCCESSFULLY DOWNLOADED.")
            self.plugin.send_notification(nanome.util.enums.NotificationTypes.success, "Successfully imported from LabArchive")
        self.plugin.add_bonds([complex], upload, True)
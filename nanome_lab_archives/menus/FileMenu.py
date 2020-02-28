import os
import datetime
import re
from functools import partial
import nanome
import imgkit

from ..IOManager import IOManager
from ..LAClient import LAClient, Tree, Entries

DIR_PATH = os.path.dirname(os.path.normpath(os.path.join(os.path.realpath(__file__), '..')))
FILES_MENU_PATH = os.path.join(DIR_PATH, 'menus', 'json', 'file.json')
ENTRY_TYPES_PATH = os.path.join(DIR_PATH, 'menus', 'json', 'entrytypes.json')

class FileMenu:
    supported_entry_types = ['heading', 'plain text entry', 'rich text entry', 'Attachment']
    def __init__(self, plugin, file=None):
        self.__plugin = plugin
        self.__menu = nanome.ui.Menu.io.from_json(FILES_MENU_PATH)
        self.__menu._index = 1
        self.__scroll_view = self.__menu.root.find_node('Entries').get_content()

        self.__file = file

        self.__entry_types = nanome.ui.LayoutNode.io.from_json(ENTRY_TYPES_PATH)

    def open_menu(self, file=None):
        self.__file = self.__file or file
        if self.__file is not None:
            self.display_file_contents()
        self.__menu.unusable = True
        self.__plugin.menu = self.__menu
        self.__plugin.update_menu(self.__menu)

    def display_file_contents(self):
        self.__menu.title = f'LA - {self.__file.name}'
        self.__scroll_view.items = []
        (err, res) = Tree.get_entries_for_page(self.__file.tree_id, self.__file.nbid, True)
        if err is None:
            entries = res['tree-tools']['entries']['entry']
            entry = entries.pop()
            while len(entries) >= 1:
                ln_entry = self.create_entry(entry)
                self.__scroll_view.items.append(ln_entry)
                entry = entries.pop()
            self.__scroll_view.items = [e for e in reversed(self.__scroll_view.items)]

    def create_entry(self, entry):
        entry_type = entry['part-type'] if entry['part-type'] in FileMenu.supported_entry_types else 'no support'
        ln_entry = self.__entry_types.find_node(entry_type).clone()
        self.give_header(entry, ln_entry)

        if entry_type == 'heading':
            self.make_entry_heading(entry, ln_entry)
        elif entry_type == 'plain text entry':
            self.make_entry_plain_text(entry, ln_entry)
        elif entry_type == 'rich text entry':
            self.make_entry_rich_text(entry, ln_entry)
        elif entry_type == 'Attachment':
            self.make_entry_attachment(entry, ln_entry)
        else:
            self.make_entry_not_supported(entry, ln_entry)

        return ln_entry

    def give_header(self, entry, ln_entry):
        update_author = entry['last-modified-by']
        update_time = datetime.datetime.strptime(entry['updated-at']['#text'], '%Y-%m-%dT%H:%M:%SZ')
        # update_time.
        ln_entry.find_node('label').get_content().text_value = f'{update_author}, {update_time}'

    def make_entry_heading(self, entry, ln_entry):
        entry_data = entry['entry-data']
        ln_entry.find_node('content').get_content().text_value = entry_data

    def make_entry_plain_text(self, entry, ln_entry):
        entry_data = entry['entry-data']
        ln_entry.find_node('content').get_content().text_value = entry_data

    def make_entry_rich_text(self, entry, ln_entry):
        entry_data = entry['entry-data']
        try:
            if bool(re.match('<.*>', entry_data)) == True:
                config = imgkit.config(wkhtmltoimage='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltoimage.exe')
                file = IOManager.get_file(entry['eid'][0:9], True)
                imgkit.from_string(entry_data, file.name, config=config)
                ln_entry.find_node('content').add_new_image(file.name)
        except OSError as e:
            print(e)

    def make_entry_attachment(self, entry, ln_entry):
        if entry['attach-content-type'] == 'chemical/x-pdb':
            ln_entry.find_node('content').get_content().set_all_text(entry['attach-file-name'])
            ln_entry.find_node('content').get_content().register_pressed_callback(partial(self.download_attachment, entry))

    def make_entry_not_supported(self, entry, ln_entry):
        ln_entry.find_node('content').get_content().text_value = 'Entry type not yet supported'

    def download_attachment(self, entry, button):
        def upload(complexes):
            self.__plugin.add_to_workspace(complexes)
            self.__plugin.send_notification(nanome.util.enums.NotificationTypes.success, "Successfully imported from LabArchive")
            button.unusable = False
            self.__plugin.update_menu(self.__menu)

        eid = entry['eid']
        name = entry['attach-file-name']
        last_modified_by = entry['last-modified-by']
        
        (err, res) = Entries.entry_attachment(eid)
        with open(name, 'w') as attachment:
            attachment.write(res)
        button.unusable = True
        self.__plugin.update_menu(self.__menu)
        complex = nanome.structure.Complex.io.from_pdb(path=name)
        complex.name = name.split('.', 1)[0]
        complex._remarks = {'Last Modified By': last_modified_by}
        self.__plugin.add_bonds([complex], upload, True)
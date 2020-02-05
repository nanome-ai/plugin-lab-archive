class Notebook:
    def __init__(self, nbid, name):
        self.nbid = nbid
        self.name = name
        self.items = []

    def add_folder(self, folder):
        folders.append(folder)

    def add_file(self, file):
        files.append(file)

    @staticmethod
    def parse(notebooks_raw):
        notebooks = []
        notebooks_raw.pop('@type')
        while len(notebooks_raw.items()) > 0:
            notebook_raw = notebooks_raw.pop('notebook')
            notebook = Notebook(notebook_raw['id'], notebook_raw['name'])
            notebooks.append(notebook)
        return notebooks

    @staticmethod
    def update_notebook(notebook, level_info, entrypoint):
        items = Tree.parse(notebook.nbid, level_info)
        entrypoint.items = items

class Tree:
    @staticmethod
    def parse(nbid, tree_raw):
        items = []
        nodes = tree_raw['tree-tools']['level-nodes']['level-node']
        if not isinstance(nodes, list):
            nodes = [nodes]

        while nodes:
            node = nodes.pop()
            # print('node:', node)
            if node['is-page']['#text'] == 'true':
                file = File.parse(node)
                file.nbid = nbid
                items.append(file)
            else:
                folder = Folder.parse(node)
                folder.nbid = nbid
                items.append(folder)
        return [e for e in reversed(items)]

class Folder:
    def __init__(self, tree_id, name):
        self.nbid = None
        self.tree_id = None
        self.name = name
        self.items = []

    def add_folder(self, folder):
        items.append(folder)

    def add_file(self, file):
        items.append(file)

    @staticmethod
    def parse(node_raw):
        folder = Folder(node_raw['tree-id'], node_raw['display-text'])
        return folder

class File:
    def __init__(self, tree_id, name):
        self.nbid = None
        self.tree_id = tree_id
        self.name = name
        self.content = ""

        self.can_read = None
        self.can_write = None
        self.can_read_comments = None
        self.can_write_comments = None

    def add_content(self, content):
        self.content += content

    @staticmethod
    def parse(node_raw):
        file = File(node_raw['tree-id'], node_raw['display-text'])
        file.can_read = node_raw['user-access']['can-read']
        file.can_write = node_raw['user-access']['can-write']
        file.can_read_comments = node_raw['user-access']['can-read-comments']
        file.can_write_comments = node_raw['user-access']['can-write-comments']
        return file
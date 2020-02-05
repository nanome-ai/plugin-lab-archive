import tempfile
import shutil

class IOManager:
    __all_files = {}
    __temp_dir = tempfile.TemporaryDirectory()

    @staticmethod
    def get_file(name, override=False):
        if name in IOManager.__all_files:
            return IOManager.__all_files[name][-1]

        file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdb", dir=IOManager.__temp_dir.name)
        if override:
            IOManager.__all_files[name] = [file]
        else:
            IOManager.__all_files[name].append(file)

        return file

    @staticmethod
    def cleanup():
        shutil.rmtree(IOManager.__temp_dir.name)
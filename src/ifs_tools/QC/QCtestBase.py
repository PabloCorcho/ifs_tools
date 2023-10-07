import yaml

from ifs_tools.html_tools.utils import HTMLPage

class QCtestBase(object):
    """Base class for Quality Control plots."""
    data_container = None

    def __init__(self, data_level, **kwargs):
        self.data_level = data_level
        self.name = kwargs.get("name", "*name*?")
        self.survey = kwargs.get("survey", "*unknown*?")
        self.html = kwargs.get("html", False)

        if self.html:
            self.html_page = HTMLPage(
                title=f"QC report of {self.name} ({self.survey})"
            )
        else:
            self.html_page = None

    def load_yml_file(self, file_path):
        with open(file_path, 'r') as file:
            content = yaml.safe_load(file)
        return content

    def check_header(self, key_dict, hdul_idx=0):
        info = self.data_container.get_from_header(key_dict.keys(),
                                         hdul_idx=hdul_idx)
        checks = []
        for k, v, in info.items():
            okey = True
            if type(v) is not str and key_dict[k] != "None":
                okey = key_dict[k][0] < v < key_dict[k][1]
            elif type(v) is str and key_dict[k] != "None":
                okey = v == key_dict[k][0]
            else:
                okey = "N/A"
            checks.append((k, v, okey))
            # print(f"{k}: {v} -- Okey: {okey}")
        return checks
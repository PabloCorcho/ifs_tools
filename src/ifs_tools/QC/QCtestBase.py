from weave.html_tools.utils import HTMLPage

class QCtestBase(object):
    """Base class for Quality Control plots."""
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
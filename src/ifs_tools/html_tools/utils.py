
def create_html_image(image_path):
    return f'<img src="{image_path}" alt="Image">'

def create_html_section(title, contents):
    return f"""
    <section>
        <h2>{title}</h2>
        {contents}
    </section>"""

def create_html_table(data):
    html = "<table>\n"

    html +="<tr>"
    for key, val in data.items():
        html += f"<td>{key}</td><td>{val}</td>"
    html += "</tr>\n"
    html += "</table>"

    return html

def create_html_page(title="UNKNOWN", content=""):
    html_template = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        {content}
    </body>
    </html>
    '''
    return html_template

class HTMLPage(object):
    def __init__(self, path=None, title="", content="") -> None:
        if path is not None:
            self.load_page(path)
        else:
            self.title = title
            self.page_src = create_html_page(title, content)

    def load_page(self, path):
        print("Loading HTML page")
        with open(path, "r") as f:
            self.page_src = f.read()
        title_pos_ini = self.page_src.find("<title>")
        title_pos_end = self.page_src.find("</title>")
        self.title = self.page_src[title_pos_ini + 7:title_pos_end]

    def add_reference(self, path, name="name"):
        print("Including reference {path}")
        pos = self.page_src.find("</body>")
        self.page_src = (self.page_src[:pos]
                         + f"<a href=\"{path}\">{name}</a>\n"
                         + self.page_src[pos:])
    
    def add_table_section(self, title, data, desc=""):
        pos = self.page_src.find("</body>")
        table_html = create_html_table(data)
        section_html = create_html_section(
            title, table_html)
        self.page_src = (self.page_src[:pos]
                         + section_html
                         + self.page_src[pos:])

    def add_plot_section(self, title, img_path, desc=""):
        pos = self.page_src.find("</body>")
        plot_html = create_html_image(img_path)
        section_html = create_html_section(
            title, plot_html)
        self.page_src = (self.page_src[:pos]
                         + section_html
                         + self.page_src[pos:])

    def save_page(self, output_path):
        print(f"Saving page as {output_path}")
        with open(output_path, "w") as f:
            f.write(self.page_src)
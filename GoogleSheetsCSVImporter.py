import requests


class GoogleSheetsCSVImporter:
    """
    I think it does not only work with Google Sheets, but it is my current purpose
    """
    link = ""
    filename = "./files/to_export.csv"

    def __init__(self, link):
        self.link = link

    def import_csv(self):
        r = requests.get(self.link)
        data = r.content
        with open(self.filename, "wb") as f:
            f.write(data)
        return self.filename
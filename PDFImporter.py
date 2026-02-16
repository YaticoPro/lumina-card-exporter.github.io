import os

from fpdf import FPDF

class PDFImporter:
    def __init__(self, card_height=88, card_width=63, vertical_margin=8, horizontal_margin=5):
        self.card_height = card_height
        self.card_width = card_width
        self.vertical_margin = vertical_margin
        self.horizontal_margin = horizontal_margin

    def import_images(self, images):
        pdf = FPDF()
        images_batch = [images[i:i+9] for i in range(0, len(images), 9)]
        for batch in images_batch:
            pdf.add_page()
            for i, image in enumerate(batch):
                py, px = i % 3, i // 3
                x = (px*self.card_width + (px+1)*self.horizontal_margin)
                y = py*self.card_height + (py+1)*self.vertical_margin
                pdf.image(image, x=x, y=y, w=self.card_width, h=self.card_height)
        pdf.output("./pdf_files/test.pdf")

    def import_from_images_directory(self, images_directory):
        files = os.listdir(images_directory, )
        self.import_images([f"{images_directory}{file}" for file in files])

if __name__ == "__main__":
    pi = PDFImporter()
    pi.import_from_images_directory("./images/")

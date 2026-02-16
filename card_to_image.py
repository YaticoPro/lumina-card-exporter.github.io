import os
import re

from PIL import Image, ImageDraw, ImageFont
import pickle

from CardImporter import Card, Cost


def from_pickle(pickle_file) -> Card:
    with open(pickle_file, "rb") as f:
        return pickle.load(f)

def int_tuple(x):
    return int(x[0]), int(x[1])

str_to_element = {
    "F": "fire",
    "G": "ice",
    "E": "lightning",
    "O": "water",
    "N": "nature",
    "T": "darkness",
    "neutral": "neutral"
}

str_to_identity = {
    "Eclair": "lightning",
    "Feu": "fire",
    "Eau": "water",
    "Glace": "ice",
    "Nature": "nature",
    "Ténèbres": "darkness"
}

effect_keywords = ["Rage", "Dissipation", "Impulsion", "Camouflage", "Furtif", "Réactive", "Aura", "Interception",
                   "Hymne", "Furie"]
effect_keywords_next = ["Croissance", "Gel", "Soin", "Silence"]

class ImageCardImporter:
    image_directory = "./images/"
    cards_directory = "./cards/"
    elements_directory = "./card_elements/"
    image_elements_directory = elements_directory + "image_elements/"
    police_elements_directory = elements_directory + "fonts/"

    def __init__(self):
        self.reset_base()

    def reset_base(self):
        self.base = Image.open(f"{self.image_elements_directory}image_background.png")
        self.draw = ImageDraw.Draw(self.base)
        self.width, self.height = self.base.size # (744, 1039)

        self.h_margin, self.v_margin = 30, 15

        self.title_font_size = 60
        self.title_font_filename = "Calvera Personal Use Only.ttf"

        self.version_font_size = 50
        self.version_font_filename = "Montserrat-Regular.ttf"

        self.effect_font_size = 45
        self.effect_font_filename = "Montserrat-Regular.ttf"
        self.effect_bold_effect_filename = "Montserrat-Extrabold.ttf"
        self.effect_height = 320

        self.image_height = 450

        self.cost_gap = 92
        self.cost_image_size = int(self.cost_gap * 5 / 8)

        self.h_limit_margin = self.width - self.h_margin
        self.margin_width = self.width - 2 * self.h_margin

    def transform_card(self, card_path=None):
        card = from_pickle(self.cards_directory + card_path)
        if not card.title:
            return

        # Frame
        xys = (0, 0), (self.width - 5, self.height - 2)
        self.draw.rectangle(xys, outline="black", fill="white", width=3)

        # Title
        xys = (self.h_margin, self.v_margin), int_tuple((self.h_limit_margin, self.v_margin + self.title_font_size * 4 / 3))
        self.add_text_in_rectangle(f"{card.title}", self.title_font_size, xys)

        # Artwork / Identity
        base_pos = xys[1][1] + self.v_margin
        xys = (self.h_margin, base_pos), int_tuple((self.h_limit_margin, base_pos + self.image_height))
        self.draw.rectangle(xys, outline="black", fill="white")

        resize_dim = (xys[1][0]-xys[0][0]-10, xys[1][1]-xys[0][1]-10)
        nb_identities = len(card.identity)
        resize_dim_multi = int_tuple((resize_dim[0] / nb_identities, resize_dim[1] / nb_identities))

        if nb_identities == 0:
            artwork = Image.open(f"{self.image_elements_directory}no_artwork.png")
            artwork = artwork.crop((78, 0, 422, 500))
            artwork = artwork.resize(resize_dim).convert("RGBA")
            self.base.paste(artwork, (xys[0][0]+5, xys[0][1]+5), mask=artwork)
        else:
            for i, identity in enumerate(card.identity):
                artwork = Image.open(f"{self.image_elements_directory}{str_to_identity[identity]}.png")
                artwork = artwork.crop((0, 78, 500, 404))
                artwork = artwork.resize(resize_dim_multi).convert("RGBA")
                self.base.paste(artwork, int_tuple((xys[0][0]+5 + resize_dim_multi[0] * i, xys[0][1] + (nb_identities>1) * resize_dim_multi[1] // nb_identities )), mask=artwork)

        # Type + Class
        base_pos = xys[1][1] + self.v_margin
        xys = (self.h_margin, base_pos), int_tuple((self.h_limit_margin, base_pos + self.title_font_size * 4 / 3))
        if card.card_class != "":
            self.add_text_in_rectangle(f"{card.card_type}  -  {card.card_class}", self.title_font_size, xys)
        else:
            self.add_text_in_rectangle(f"{card.card_type}", self.title_font_size, xys)

        # Effect
        base_pos = xys[1][1] + self.v_margin
        xys = (self.h_margin, base_pos), (self.h_limit_margin, base_pos + self.effect_height)
        self.draw.rectangle(xys, outline="black", fill="white")
        middle = int_tuple(((xys[0][0]+xys[1][0])/2, (xys[0][1]+xys[1][1])/2))
        max_width = xys[1][0] - xys[0][0] - 2 * self.h_margin
        # self.draw.multiline_text(middle, "\n".join(self.wrap_text(card.effect, font, bold_font, max_width)[0]), font=font, fill="blue", anchor="mm", align="center")
        self.custom_multiline_text(card.effect, middle, self.effect_font_filename, self.effect_bold_effect_filename, max_width, fill="black")

        # Atk / Def
        base_pos = xys[1][1] - 2.5 * self.v_margin
        xys = (480, base_pos), (730, base_pos + self.title_font_size * 4 / 3)
        if card.card_type == "Unité":
            self.add_text_in_rectangle(f"{card.attack}  /  {card.defense}", self.title_font_size, xys)

        # Cost
        for i, cost in enumerate(card.cost):
            element, value = cost
            element_image = Image.open(self.image_elements_directory + str_to_element[element] + ".png")
            element_image = element_image.crop((75,75,425,425))
            element_image = element_image.resize((self.cost_image_size, self.cost_image_size)).convert("RGBA")
            self.base.paste(element_image, (35 + i*self.cost_gap, 115), mask=element_image)
            xys_element = ((30 + self.cost_image_size + i*self.cost_gap, 115),
                           (30 + self.cost_image_size + i*self.cost_gap + 30, 115 + self.cost_image_size))
            self.add_text_in_rectangle(f"{value}", self.effect_font_size, xys_element, margin = False, rectangle=False)

        # Nation
        base_pos = 180
        if card.nation != "":
            xys_nation = ((480, base_pos),(730, base_pos + self.title_font_size * 4 / 3))
            self.add_text_in_rectangle(f"{card.nation}", self.title_font_size, xys_nation)

        # Swiftness
        if card.swiftness == "Rapide":
            swiftness_image = Image.open(f"{self.image_elements_directory}swiftness.png").resize((130, 182))
            swiftness_image = swiftness_image.convert("RGBA")
            self.base.paste(swiftness_image, (570, 430), mask=swiftness_image)

        # Extension / Version
        base_pos = xys[1][1] - self.v_margin / 2 - 2 * self.v_margin
        xys = (10, base_pos), int_tuple((100, self.height - 10))
        self.add_text_in_rectangle(f"{card.extension} - v{card.version}", self.version_font_size, xys, font=self.version_font_filename, margin=False, rectangle=False)

        # Save
        self.base.save(f"{self.image_directory}{card.id}.png")

    def custom_multiline_text(self, text, position, font_filename, bold_font_filename, max_width, fill="black"):
        if text == "":
            return

        font = ImageFont.truetype(self.police_elements_directory + font_filename, self.effect_font_size)
        bold_font = ImageFont.truetype(self.police_elements_directory + bold_font_filename, self.effect_font_size)

        lines, widths = self.wrap_text(text, font, bold_font, max_width)
        max_lines = 5
        if len(lines) > max_lines:
            r = len(lines) / (max_lines + 1)
            font_size = int(self.effect_font_size / r)
            font = ImageFont.truetype(self.police_elements_directory + font_filename, font_size)
            bold_font = ImageFont.truetype(self.police_elements_directory + bold_font_filename, font_size)
            lines, widths = self.wrap_text(text, font, bold_font, max_width)

        x, y = position
        total_height = 0

        for line in lines:
            words = line.split()
            line_height = max(font.getbbox(word)[3] for word in words)
            total_height += line_height

        y_start = y - total_height // 2
        if len(lines) > 4:
            y_start -= line_height // 3

        for line, width in zip(lines, widths):
            words = line.split()
            current_x = x - width // 2
            line_height = max(font.getbbox(word)[3] for word in words)

            for word in words:
                font_to_use = font
                if word in effect_keywords or word in effect_keywords_next or (words.index(word) > 0 and words[words.index(word)-1] in effect_keywords_next):
                    font_to_use = bold_font

                bbox = font_to_use.getbbox(word)
                word_width = bbox[2] - bbox[0]
                self.draw.text((current_x, y_start), word, font=font_to_use, fill=fill)
                current_x += word_width + font_to_use.getbbox(" ")[2]

            y_start += line_height

    def add_text_in_rectangle(self, text, text_font_size, xys, font=None, rectangle=True, margin=True):
        if rectangle:
            self.draw.rectangle(xys, outline="black", fill="white")
        if font is None:
            font = self.title_font_filename
        title_font = ImageFont.truetype(self.police_elements_directory + font, text_font_size)
        text_length = self.draw.textlength(text, title_font, font_size=text_font_size)
        max_width = xys[1][0] - xys[0][0]
        max_width -= 2 * self.h_margin if margin else 0
        if text_length > max_width:
            r = text_length / max_width
            text_font_size = text_font_size / r
            title_font = ImageFont.truetype(self.police_elements_directory + font, text_font_size)
            text_length = self.draw.textlength(text, title_font, font_size=text_font_size)
        pxpy = (xys[0][0] + xys[1][0]) / 2 - text_length / 2, (xys[0][1] + xys[1][1]) / 2 - text_font_size * 4 / 6
        self.draw.text(pxpy, font=title_font, text=text, fill="black")

    def draw_text_in_font(self, coords: tuple[int, int],
                          content: list[tuple[str, tuple[int, int, int], str, int]]):
        fonts = {}
        for text, color, font_name, font_size in content:
            font = fonts.setdefault(font_name, ImageFont.truetype(font_name, font_size))
            self.draw.text(coords, text, color, font)
            coords = (coords[0] + font.getsize(text)[0], coords[1])

    def wrap_text(self, text, font, bold_font, max_width):
        words = text.split()
        lines = []
        current_line = []
        widths = []
        width = 0
        for i in range(len(words)):
            word = words[i]
            font_to_use = font
            if word in effect_keywords or i > 1 and words[i-1] in effect_keywords_next:
                font_to_use = bold_font
            test_line = ' '.join(current_line + [word])
            last_width, width = width, self.draw.textlength(test_line, font=font_to_use)
            if width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                width = self.draw.textlength(word, font=font_to_use)
                widths.append(last_width)
                current_line = [word]

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
            widths.append(width)

        return lines, widths

    def transform_cards(self, directory_path, limit=None):
        regex_file_format = re.compile(r"^([0-9a-z]+)\.pickle$")
        cards_paths = os.listdir(directory_path)
        i = 0
        for card_path in cards_paths:
            if regex_file_format.match(card_path):
                self.transform_card(card_path)
                i += 1
                if limit is not None and i >= limit:
                    break
                self.reset_base()

if __name__ == "__main__":
    ici= ImageCardImporter()
    ici.transform_cards(ici.cards_directory)

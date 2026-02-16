import os

from PIL import Image, ImageDraw, ImageFont
import pickle

from CardImporter import Card


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

effect_keywords = ["Rage", "Dissipation", "Impulsion", "Camouflage", "Furtif", "Réactive", "Aura",
                   "Silence", "Interception", "Hymne", "Furie"]
effect_keywords_next = ["Croissance", "Gel", "Soin"]

class ImageCardImporter:
    image_directory = "./images/"
    cards_directory = "./cards/"
    elements_directory = "./card_elements/"
    image_elements_directory = elements_directory + "image_elements/"
    police_elements_directory = elements_directory + "fonts/"

    # Charger fond image
    # Ajouter chacun des éléments
    ## Titre
    ## Coût
    ## Artwork
    ## Classe et Peuple
    ## Texte
    ## Atk / Def
    ## Rapidité

    def __init__(self):
        self.reset_base()

    def reset_base(self):
        self.base = Image.open(f"{self.image_elements_directory}image_background.png")
        self.draw = ImageDraw.Draw(self.base)
        self.width, self.height = self.base.size # (744, 1039)

        self.h_margin, self.v_margin = 30, 15

        self.title_font_size = 60
        self.title_font_filename = "Calvera Personal Use Only.ttf"

        self.base_font_size = 20
        self.base_font_filename = "Calvera Personal Use Only.ttf"

        self.effect_font_size = 45
        self.effect_font_filename = "Montserrat-Regular.ttf"
        self.effect_bold_effect_filename = "Montserrat-Bold.ttf"
        self.effect_height = 320

        self.image_height = 450

        self.cost_gap = 80
        self.cost_image_size = int(self.cost_gap * 5 / 8)

        self.h_limit_margin = self.width - 2 * self.h_margin
        self.margin_width = self.width - 2 * self.h_margin

    def transform_card(self, card_path=None):
        card = from_pickle(self.cards_directory + card_path)

        # Frame
        xys = (0, 0), (self.width - 5, self.height - 2)
        self.draw.rectangle(xys, outline="black", fill="white", width=3)

        # Title
        xys = (self.h_margin, self.v_margin), int_tuple((self.margin_width, self.v_margin + self.title_font_size * 4 / 3))
        self.add_text_in_rectangle(f"{card.title}", self.title_font_size, xys)

        # Artwork
        base_pos = xys[1][1] + self.v_margin
        xys = (self.h_margin, base_pos), int_tuple((self.h_limit_margin, base_pos + self.image_height))
        self.draw.rectangle(xys, outline="black", fill="white")
        artwork = Image.open(f"{self.image_elements_directory}no_artwork.png") # TODO change to artwork
        artwork = artwork.resize((xys[1][0]-xys[0][0]-10, xys[1][1]-xys[0][1]-10))
        self.base.paste(artwork, (xys[0][0]+5, xys[0][1]+5))

        # Nation + Class
        base_pos = xys[1][1] + self.v_margin
        xys = (self.h_margin, base_pos), int_tuple((self.h_limit_margin, base_pos + self.title_font_size * 4 / 3))
        if card.card_type == "Unité":
            self.add_text_in_rectangle(f"{card.card_class}  -  {card.nation}", self.title_font_size, xys)
        elif card.card_type == "Structure":
            self.add_text_in_rectangle(f"{card.nation}", self.title_font_size, xys)
        else:
            self.add_text_in_rectangle(f"{card.card_type}", self.title_font_size, xys)

        # Effect
        base_pos = xys[1][1] + self.v_margin
        xys = (self.h_margin, base_pos), (self.h_limit_margin, base_pos + self.effect_height)
        self.draw.rectangle(xys, outline="black", fill="white")
        font = ImageFont.truetype(self.police_elements_directory + self.effect_font_filename, self.effect_font_size)
        bold_font = ImageFont.truetype(self.police_elements_directory + self.effect_bold_effect_filename, self.effect_font_size)
        middle = int_tuple(((xys[0][0]+xys[1][0])/2, (xys[0][1]+xys[1][1])/2))
        max_width = xys[1][0] - xys[0][0] - 2 * self.h_margin
        self.draw.multiline_text(middle, self.wrap_text(card.effect, font, bold_font, max_width), font=font, fill="black", anchor="mm", align="center")

        # Atk / Def
        base_pos = xys[1][1] - 4 * self.v_margin
        xys = (480, base_pos), (730, base_pos + self.title_font_size * 4 / 3)
        if card.card_type == "Unité":
            self.add_text_in_rectangle(f"{card.attack} / {card.defense}", self.title_font_size, xys)

        # Cost
        for i, cost in enumerate(card.cost):
            element, value = cost
            element_image = Image.open(self.image_elements_directory + str_to_element[element] + ".png")
            element_image = element_image.resize((self.cost_image_size, self.cost_image_size)).convert("RGBA")
            self.base.paste(element_image, (35 + i*self.cost_gap, 115), mask=element_image)
            xys_element = (35 + self.cost_image_size + i*self.cost_gap, 115), (35 + self.cost_image_size + i*self.cost_gap+30, 115 + self.cost_image_size)
            self.add_text_in_rectangle(f"{value}", self.effect_font_size, xys_element, margin = False)

        # Swiftness
        if card.swiftness == "Rapide":
            swiftness_image = Image.open(f"{self.image_elements_directory}swiftness.png").resize((130, 182))
            swiftness_image = swiftness_image.convert("RGBA")
            self.base.paste(swiftness_image, (570, 430), mask=swiftness_image)


        # Extension / Version
        base_pos = xys[1][1] - self.v_margin / 2
        xys = (10, base_pos), int_tuple((100, base_pos + self.base_font_size * 4 / 3))
        self.add_text_in_rectangle(f"{card.extension} - v{card.version}", self.base_font_size, xys)


        self.base.save(f"{self.image_directory}{card.id}.png")

    def add_text_in_rectangle(self, text, text_font_size, xys, rectangle=True, margin=True):
        if rectangle:
            self.draw.rectangle(xys, outline="black", fill="white")
        title_font = ImageFont.truetype(self.police_elements_directory + self.title_font_filename, text_font_size)
        text_length = self.draw.textlength(text, title_font, font_size=text_font_size)
        max_width = xys[1][0] - xys[0][0]
        max_width -= 2 * self.h_margin if margin else 0
        if text_length > max_width:
            r = text_length / max_width
            text_font_size = text_font_size / r
            title_font = ImageFont.truetype(self.police_elements_directory + self.title_font_filename, text_font_size)
            text_length = self.draw.textlength(text, title_font, font_size=text_font_size)
        pxpy = (xys[0][0]+xys[1][0])/2 - text_length/2, (xys[0][1]+xys[1][1])/2 - text_font_size * 4 / 6
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
        lines = [] # Holds each line in the text box
        current_line = [] # Holds each word in the current line under evaluation.

        for i in range(len(words)):
            word = words[i]
            font_to_use = font
            if word in effect_keywords or i > 1 and words[i-1] in effect_keywords_next:
                font_to_use = bold_font
            # Check the width of the current line with the new word added
            test_line = ' '.join(current_line + [word])
            width = self.draw.textlength(test_line, font=font_to_use)
            if width <= max_width:
                current_line.append(word)
            else:
                # If the line is too wide, finalize the current line and start a new one
                lines.append(' '.join(current_line))
                current_line = [word]

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))

        return "\n".join(lines)

    def transform_cards(self, directory_path, limit=None):
        cards_paths = os.listdir(directory_path)
        i = 0
        for card_path in cards_paths:
            self.transform_card(card_path)
            i += 1
            if limit is not None and i >= limit:
                break
            self.reset_base()


if __name__ == "__main__":
    ici= ImageCardImporter()
    ici.transform_cards(ici.cards_directory, limit=5)

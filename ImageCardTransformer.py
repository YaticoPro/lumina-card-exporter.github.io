import os
import json

from PIL import Image, ImageDraw, ImageFont, ImageColor
import pickle

if not 'Card' in dir():
    from CardImporter import Card

def from_pickle(pickle_file) -> Card:
    with open(pickle_file, "rb") as f:
        return pickle.load(f)

def int_tuple(x):
    return int(x[0]), int(x[1])

cost_to_identity = {
    "F": "Feu",
    "G": "Glace",
    "E": "Eclair",
    "O": "Eau",
    "N": "Nature",
    "T": "Ténèbres",
    "neutral": "Neutre"
}

identity_to_image = {
    "Eclair": "lightning",
    "Feu": "fire",
    "Eau": "water",
    "Glace": "ice",
    "Nature": "nature",
    "Ténèbres": "darkness",
    "Neutre": "neutral"
}

identity_to_color = {
    "Eclair": "gold",
    "Feu": "coral",
    "Eau": "royalblue",
    "Glace": "lightblue",
    "Nature": "lightgreen",
    "Ténèbres": "rebeccapurple",
    "Neutre": "silver"
}

effect_keywords = ["Rage", "Dissipation", "Impulsion", "Camouflage", "Furtif", "Réactive", "Aura", "Interception",
                   "Hymne", "Furie"]
effect_keywords_next = ["Croissance", "Gel", "Soin", "Silence"]

class ImageCardTransformer:
    """
    Class transforming the Card (from a pickle format) into
    """
    base, draw, width, height, cost_image_size, cost_gap, h_margin, v_margin, h_limit_margin, margin_width = [None]*10
    title_font_size, effect_font_size, image_height, effect_font_filename, effect_bold_effect_filename, effect_height = [None]*6
    version_font_size, version_font_filename, title_font_filename = [None]*3
    image_directory = "./images/"
    cards_directory = "./cards/"
    elements_directory = "./card_elements/"
    image_elements_directory = elements_directory + "image_elements/"
    police_elements_directory = elements_directory + "fonts/"
    json_config = elements_directory + "/config.json"

    def __init__(self):
        self.reset_base()

    def reset_base(self):
        self.base = Image.open(f"{self.image_elements_directory}image_background.png")
        self.draw = ImageDraw.Draw(self.base)

        with open(f"{self.json_config}", "r") as f:
            json_config = json.load(f)
            for k, v in json_config.items():
                setattr(self, k, v)

        assert self.base.size == (self.width, self.height)

        self.cost_image_size = int(self.cost_gap * 5 / 8)

        self.h_limit_margin = self.width - self.h_margin
        self.margin_width = self.width - 2 * self.h_margin

    def transform_card(self, card_path):
        card = from_pickle(self.cards_directory + card_path)
        if not card.title:
            return

        # Frame
        xys = (0, 0), (self.width - 5, self.height - 2)
        identity_polygons = [[[0,0,744,0,744,1039,0,1039]],
                        [[0,0,744,0,0,1039],[744,0,0,1039,744,1039]],
                        [[0,0,744,0,0,520],[744,0,744,520,0,1039,0,520],[744,520,744,1039,0,1039]]]
        nb_identity = len(card.identity)
        if nb_identity > 0:
            for i in range(nb_identity):
                self.draw.polygon(identity_polygons[nb_identity-1][i], fill=identity_to_color[card.identity[i]])
        else:
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
        offset_nb_identities = [[0], [-50, 50], [-50,20,90]]
        for i, identity in enumerate(card.identity):
            artwork = Image.open(f"{self.image_elements_directory}{identity_to_image[identity]}.png")
            artwork, binary = self.normalize_artwork(artwork, resize_dim_multi, color=identity_to_color[identity])
            artwork.save("test.png")
            self.base.paste(artwork, int_tuple((xys[0][0]+5 + resize_dim_multi[0] * i, (xys[0][1]+xys[1][1])/2 - resize_dim_multi[1] / 2 + offset_nb_identities[nb_identities-1][i])), mask=binary)

        # Swiftness
        if card.swiftness == "Rapide":
            swiftness_resize_dim = (103,75)
            swiftness_image = Image.open(f"{self.image_elements_directory}swiftness.png").resize(swiftness_resize_dim)
            swiftness_image = swiftness_image.convert("RGBA")
            self.base.paste(swiftness_image, (xys[1][0] - swiftness_resize_dim[0] - self.h_margin // 2, xys[1][1] - swiftness_resize_dim[1] - self.v_margin), mask=swiftness_image)

        # Type + Class
        base_pos = xys[1][1] + self.v_margin
        xys = (self.h_margin, base_pos), int_tuple((self.h_limit_margin, base_pos + self.title_font_size * 4 / 3))
        self.add_text_in_rectangle(f"{card.card_type}", self.title_font_size, xys)

        # Effect
        base_pos = xys[1][1] + self.v_margin
        xys = (self.h_margin, base_pos), (self.h_limit_margin, base_pos + self.effect_height)
        self.draw.rectangle(xys, outline="black", fill="white")
        middle = int_tuple(((xys[0][0]+xys[1][0])/2, (xys[0][1]+xys[1][1])/2))
        max_width = xys[1][0] - xys[0][0] - 2 * self.h_margin
        self.custom_multiline_text(card.effect, middle, self.effect_font_filename, self.effect_bold_effect_filename, max_width, fill="black")

        # Atk / Def
        base_pos = xys[1][1] - 2.8 * self.v_margin
        xys = (480, base_pos), (730, base_pos + self.title_font_size * 4 / 3)
        if card.card_type == "Unité":
            self.add_text_in_rectangle(f"{card.attack}  /  {card.defense}", self.title_font_size, xys)

        # Cost
        for i, cost in enumerate(card.cost):
            element, value = cost
            element_image = Image.open(self.image_elements_directory + identity_to_image[cost_to_identity[element]] + ".png")
            element_image = element_image.crop((75,75,425,425))
            element_image = element_image.resize((self.cost_image_size, self.cost_image_size)).convert("RGBA")
            element_image, binary = self.change_color(element_image, identity_to_color[cost_to_identity[element]])
            self.base.paste(element_image, (35 + i*self.cost_gap, 115), mask=binary)
            xys_element = ((30 + self.cost_image_size + i*self.cost_gap, 115),
                           (30 + self.cost_image_size + i*self.cost_gap + 30, 115 + self.cost_image_size))
            self.add_text_in_rectangle(f"{value}", self.effect_font_size, xys_element, margin = False, rectangle=False)

        # Nation
        base_pos = 180
        if card.nation != "":
            xys_nation = ((480, base_pos),(730, base_pos + self.title_font_size * 4 / 3))
            self.add_text_in_rectangle(f"{card.nation}", self.title_font_size, xys_nation)

        # Class
        base_pos = 280
        if card.card_class != "":
            xys_nation = ((480, base_pos),(730, base_pos + self.title_font_size * 4 / 3))
            self.add_text_in_rectangle(f"{card.card_class}", self.title_font_size, xys_nation)

        # Extension / Version
        base_pos = xys[1][1] - self.v_margin / 2 - 2 * self.v_margin
        xys = (10, base_pos), int_tuple((100, self.height - 10))
        self.add_text_in_rectangle(f"{card.extension} - v{card.version}", self.version_font_size, xys, font=self.version_font_filename, margin=False, rectangle=False)

        # Save
        self.base.save(f"{self.image_directory}{card.id}.png")

    def normalize_artwork(self, artwork, resize_dim, color):
        artwork = artwork.crop((0, 78, 500, 404))
        artwork = artwork.resize(resize_dim).convert("RGBA")
        rgb = ImageColor.getrgb(color)
        artwork, binary = self.change_color(artwork, rgb)
        return artwork, binary

    @staticmethod
    def change_color(artwork, color):
        binary = artwork.point(lambda p: 255 if p > 150 else 0)
        colored = Image.new("RGB", artwork.size)
        colored.paste(color, mask=binary)
        return colored, binary

    def custom_multiline_text(self, text, position, font_filename, bold_font_filename, max_width, fill="black"):
        if text == "":
            return

        font = ImageFont.truetype(self.police_elements_directory + font_filename, self.effect_font_size)
        bold_font = ImageFont.truetype(self.police_elements_directory + bold_font_filename, self.effect_font_size)

        lines, widths = self.wrap_text(text, font, bold_font, max_width)
        max_lines = 5
        if len(lines) > max_lines:
            r = len(lines) / max_lines
            font_size = int(self.effect_font_size / r)
            font = ImageFont.truetype(self.police_elements_directory + font_filename, font_size)
            bold_font = ImageFont.truetype(self.police_elements_directory + bold_font_filename, font_size)
            lines, widths = self.wrap_text(text, font, bold_font, max_width)

        x, y = position
        total_height = 0

        line_height = 0
        for line in lines:
            words = line.split()
            line_height = max(font.getbbox(word)[3] for word in words)
            total_height += line_height

        y_start = y - total_height // 2
        if len(lines) > 4:
            y_start -= line_height // 3

        word_to_identify_effect = None
        for line, width in zip(lines, widths):
            words = line.split()
            current_x = x - width // 2
            line_height = max(font.getbbox(word)[3] for word in words)

            for word in words:
                last_word, word_to_identify_effect = word_to_identify_effect, word.strip(",:.")
                font_to_use = font
                if (word_to_identify_effect in effect_keywords
                        or word_to_identify_effect in effect_keywords_next
                        or last_word in effect_keywords_next and word.isdigit()):
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
        text_length = self.draw.textbbox((0,0), text, font=title_font)
        text_length = text_length[2] - text_length[0]
        max_width = xys[1][0] - xys[0][0]
        max_width -= 2 * self.h_margin if margin else 0
        if text_length > max_width:
            r = text_length / max_width
            text_font_size = int(text_font_size / r)
            title_font = ImageFont.truetype(self.police_elements_directory + font, text_font_size)
            text_length = self.draw.textbbox((0,0), text, font=title_font)
            text_length = text_length[2] - text_length[0]
        pxpy = (xys[0][0] + xys[1][0]) / 2 - text_length / 2, (xys[0][1] + xys[1][1]) / 2 - text_font_size * 4 / 6
        self.draw.text(pxpy, font=title_font, text=text, fill="black")

    def draw_text_in_font(self, coordinates: tuple[int, int],
                          content: list[tuple[str, tuple[int, int, int], str, int]]):
        fonts = {}
        for text, color, font_name, font_size in content:
            font = fonts.setdefault(font_name, ImageFont.truetype(font_name, font_size))
            self.draw.text(coordinates, text, color, font)
            coordinates = (coordinates[0] + font.getsize(text)[0], coordinates[1])

    def wrap_text(self, text, font, bold_font, max_width):
        words = text.split()
        lines = []
        current_line = []
        widths = []
        width = 0
        word_to_identify_effect = None
        for i in range(len(words)):
            word = words[i]
            if word == '|':
                lines.append(' '.join(current_line))
                widths.append(width)
                width = 0
                current_line = []
            else:
                last_word, word_to_identify_effect = word_to_identify_effect, word.strip(",:.")
                font_to_use = font
                if (word_to_identify_effect in effect_keywords
                        or word_to_identify_effect in effect_keywords_next
                        or last_word in effect_keywords_next and word.isdigit()):
                    font_to_use = bold_font
                test_line = ' '.join(current_line + [word])
                # last_width, width = width, self.draw.textlength(test_line, font=font_to_use)
                text_length = self.draw.textbbox((0,0), test_line, font=font_to_use)
                last_width, width = width, text_length[2] - text_length[0]
                if width <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    # width = self.draw.textlength(word, font=font_to_use)
                    text_length = self.draw.textbbox((0,0), word, font=font_to_use)
                    width = text_length[2] - text_length[0]
                    widths.append(last_width)
                    current_line = [word]

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
            widths.append(width)

        return lines, widths

    def transform_cards(self, directory_path=None, limit=None):
        if directory_path is None:
            directory_path = self.cards_directory
        cards_paths = os.listdir(directory_path)
        i = 0
        for card_path in cards_paths:
            self.transform_card(card_path)
            i += 1
            if limit is not None and i >= limit:
                break
            self.reset_base()

    def delete_images(self):
        for file in os.listdir(f"{self.image_directory}"):
            if file.endswith(".png"):
                os.remove(f"{self.image_directory}{file}")

if __name__ == "__main__":
    ici= ImageCardTransformer()
    ici.transform_cards(ici.cards_directory)

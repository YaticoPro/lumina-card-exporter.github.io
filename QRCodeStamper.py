import qrcode
from PIL import Image


class QRCodeStamper():
    gap_up = 0
    gap_down = 60
    gap_mult = 1.1

    def __init__(self):
        pass

    def create_qr_code(self, text) -> Image:
        img = qrcode.make(text, border=0, box_size=10)
        file_path = "aux.png"
        img.save(file_path)
        return file_path

    def stamp_qr_code(self, text, image, size, position, file_path = "aux.png") -> Image:
        qr_code = qrcode.make(text, border=0).resize(size)

        box = (position[0], position[1], position[0]+size[0], position[1]+size[1])
        image_coded = image.convert("RGBA").crop(box)
        new_image_coded = Image.new("RGBA", size)
        qr_code = qr_code.convert("RGBA")

        new_data = []
        for item_i, item_q in zip(image_coded.getdata(), qr_code.getdata()):
            if item_q[0] == 255:
                new_data.append((int(min(255,item_i[0]*self.gap_mult+self.gap_up)), int(min(255,item_i[1]*self.gap_mult+self.gap_up)), int(min(255,item_i[2]*self.gap_mult+self.gap_up)), int(max(0,item_i[3]/self.gap_mult-self.gap_up))))
            else:
                new_data.append((int(max(0,item_i[0]/self.gap_mult-self.gap_down)), int(max(0,item_i[1]/self.gap_mult-self.gap_down)), int(max(0,item_i[2]/self.gap_mult-self.gap_down)), int(min(255,item_i[3]*self.gap_mult+self.gap_down))))
        new_image_coded.putdata(new_data)
        new_image_coded.save(file_path)
        return file_path
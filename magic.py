#!/usr/bin/env python
"""
python3 magic.py &      - run
ps ax | grep magic.py   - check
pkill -f magic.py       - kill
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os
import time


FONTS = (
    "fonts/font.ttf",
    "fonts/night.ttf",
    "fonts/angel.otf",
    "fonts/star_trek.ttf",
    "fonts/bloodcrow.ttf",
)

MARK = 'water\nmark'
OPACITY = 0.6  # [0, 1]
FONT = FONTS[0]
SCALE = 0.05
COLOR = (255, 255, 255)
ALIGN = 'center'  # left, right or center
MARGIN = (10, 10)

LOOP_TIME = 5

USE_STROKE = True
STROKE_COLOR = (255, 125, 0)
STROKE_SIZE = 3


watermarked_path = 'watermarked'
images_path = 'images'
done_path = images_path + '/.done.txt'


class ImproperlyConfigured(Exception):
    pass


def reduce_opacity(image, opacity):
    """
    Returns an image with reduced opacity.
    """
    assert 0 <= opacity <= 1
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    else:
        image = image.copy()
    alpha = image.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    image.putalpha(alpha)
    return image


def imprint(image, text, font=None, color=None, opacity=0.6, margin=(0, 0)):
    """
    imprints a PIL image with the indicated text in lower-right corner
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    text_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    text_size = draw.textsize(text, font=font)
    # x, y = [image.size[i]//2 - text_size[i]//2 - margin[i] for i in (0, 1)]  # center
    x, y = [image.size[i] - text_size[i] - margin[i] for i in (0, 1)]

    b = STROKE_SIZE  # border

    if USE_STROKE:
        # thin border
        # draw.text((x - b, y), text, font=font, fill=STROKE_COLOR, align=ALIGN)
        # draw.text((x + b, y), text, font=font, fill=STROKE_COLOR, align=ALIGN)
        # draw.text((x, y - b), text, font=font, fill=STROKE_COLOR, align=ALIGN)
        # draw.text((x, y + b), text, font=font, fill=STROKE_COLOR, align=ALIGN)

        # thicker border
        draw.text((x - b, y - b), text, font=font, fill=STROKE_COLOR, align=ALIGN)
        draw.text((x + b, y - b), text, font=font, fill=STROKE_COLOR, align=ALIGN)
        draw.text((x - b, y + b), text, font=font, fill=STROKE_COLOR, align=ALIGN)
        draw.text((x + b, y + b), text, font=font, fill=STROKE_COLOR, align=ALIGN)

    # draw the text over it
    draw.text((x, y), text, font=font, fill=color, align=ALIGN)

    if 0 <= opacity < 1:
        text_layer = reduce_opacity(text_layer, opacity)
    return Image.composite(text_layer, image, mask=text_layer)


def watermark(image, text, font_path, font_scale=None, font_size=None, color=(0, 0, 0),
              opacity=0.6, margin=(0, 0)):
    """
    image - PIL Image instance
    text - text to add over image
    font_path - font that will be used
    font_scale - font size will be set as percent of image height
    """
    if font_scale and font_size:
        raise ImproperlyConfigured(
            "You should provide only font_scale or font_size option, but not both")
    elif font_scale:
        width, height = image.size
        font_size = int(font_scale*height)
    elif not (font_size or font_scale):
        raise ImproperlyConfigured("You should provide font_scale or font_size option")

    font = ImageFont.truetype(font_path, font_size)

    return imprint(image, text, font=font, opacity=opacity, color=color, margin=margin)


def remake_done_file(data=None):
    f = open(done_path, 'w')
    if data:
        for line in data:
            f.write(line)


def main():
    if not os.path.exists(watermarked_path):
        os.makedirs(watermarked_path)
    if not os.path.exists(images_path):
        os.makedirs(images_path)

    done_images = open(done_path, 'r').readlines()
    new_done_data = []

    for (dir_path, dir_names, file_names) in os.walk(images_path):
        for file_name in file_names:
            if not (str(file_name).endswith('.jpg') or
                    str(file_name).endswith('.jpeg') or
                    str(file_name).endswith('.png')):
                continue

            if (file_name + '\n') in done_images:
                new_done_data.append(file_name + '\n')
                continue

            try:
                im = Image.open("%s/%s" % (dir_path, file_name))
                result = watermark(im, MARK, color=COLOR, opacity=OPACITY,
                                   font_path=FONT, font_scale=SCALE, margin=MARGIN)
                result.save("%s/%s" % (watermarked_path, file_name))
                new_done_data.append(file_name + '\n')
            except IOError:
                print('something wrong')
                pass
    remake_done_file(new_done_data)

if __name__ == "__main__":
    remake_done_file()

    while True:
        main()
        time.sleep(LOOP_TIME)

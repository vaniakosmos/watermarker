#!/usr/bin/env python
"""
python3 charm.py &      - run
ps ax | grep magic.py   - check
pkill -f charm.py       - kill
"""

from PIL import Image, ImageEnhance
import os
import time


OPACITY = 0.5  # [0..1]
SCALE = 0.1  # [0..1]
POS = (1, 1)  # (0, 0) - left, top; (1, 1) - right, bottom
ANGLE = 0
AVERAGE = 123  # 255/2, average color between 0 and 255. It needs to choose mark color

LOOP_TIME = 5  # in seconds


patterns_path = 'patterns'
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
    alpha = image.split()[-1]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    image.putalpha(alpha)
    return image


def choose_white(image):
    w, h = image.size
    # colors = [(count, rgb color), ...]
    colors = image.getcolors(w * h)
    try:
        s_count = sum([count for count, _ in colors])
        s_color = sum([count * sum(color) for count, color in colors])
        curr_average_color = s_color / s_count / 3
        return AVERAGE > curr_average_color
    except TypeError:
        pass


def add_watermark(image, opacity=0.6, scale=0.1, pos=(0.80, 0.80), angle=0):
    """
    :param image: <PIL.Image>
    :param opacity: float [0..1]
    :param scale: float [0..1]
    :param pos: tuple(float, float)
    :param angle: int
    :return: <PIL.Image>
    """
    pattern = Image.open(patterns_path + '/white.png', 'r')
    pat_w, pat_h = pattern.size
    im_w, im_h = image.size

    # get proper size
    min_side = min(im_w, im_h)
    new_pat_width = int(scale * min_side)
    pat_w, pat_h = new_pat_width, int(pat_w / pat_h * new_pat_width)

    # get proper position
    respective_pos_x, respective_pos_y = pos
    pos_x, pos_y = (int((im_w - pat_w) * respective_pos_x),
                    int((im_h - pat_h) * respective_pos_y))

    # detect average color in cropped image
    cropped = image.crop((pos_x, pos_y, pos_x + pat_w, pos_y + pat_h))
    if not choose_white(cropped):
        pattern = Image.open(patterns_path + '/black.png', 'r')

    # actually change pattern
    pattern.thumbnail((pat_w, pat_h), Image.ANTIALIAS)
    pattern = reduce_opacity(pattern, opacity)
    pattern = pattern.rotate(angle)

    image.paste(pattern, (pos_x, pos_y), mask=pattern)
    return image


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
                image = Image.open("%s/%s" % (dir_path, file_name))
                result = add_watermark(image,
                                       opacity=OPACITY, scale=SCALE,
                                       pos=POS, angle=ANGLE)
                result.save("%s/%s" % (watermarked_path, file_name))
                new_done_data.append(file_name + '\n')
            except IOError:
                print('something wrong')
                pass
    remake_done_file(new_done_data)

if __name__ == "__main__":
    remake_done_file()
    # main()
    import time
    while True:
        main()
        time.sleep(LOOP_TIME)

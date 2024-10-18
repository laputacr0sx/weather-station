import logging
import os

from PIL import Image, ImageDraw

from weather_display import EPD_HEIGHT, EPD_WIDTH, PIC_DIR
from weather_display.lib.waveshare_epd import epd7in5_V2

logging.basicConfig(level=logging.DEBUG)


def iterate_all_pic_dir_img(
    img: Image.Image, draw: ImageDraw.ImageDraw, directory_path
):
    cell_dimension = 80
    rows, cols = EPD_HEIGHT // cell_dimension, EPD_WIDTH // cell_dimension

    icon_size = (72, 72)
    center_pos = (cell_dimension - icon_size[0]) // 2

    png_files = [file for file in os.listdir(directory_path) if file.endswith('.png')]

    idx = 0
    for y in range(rows):
        for x in range(cols):
            if idx > len(png_files):
                break
            else:
                png_file_path = os.path.join(directory_path, png_files[idx])
                idx += 1

                icon = Image.open(png_file_path)
                icon_pos = (
                    center_pos + x * cell_dimension,
                    center_pos + y * cell_dimension,
                )
                resized_icon = icon.resize(icon_size)

                draw.rectangle(
                    (
                        icon_pos[0] - 1,
                        icon_pos[1] - 1,
                        1 + icon_pos[0] + icon_size[0],
                        1 + icon_pos[1] + icon_size[1],
                    ),
                    fill=0,
                )

                img.paste(resized_icon, icon_pos)

                print(f'Loading {png_file_path}')


def main():
    epd = epd7in5_V2.EPD()

    logging.info('init and Clear')
    epd.init()
    epd.Clear()

    logging.info('Generating Image')
    main_image = Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 255)

    logging.info('Drawing Image')
    draw = ImageDraw.Draw(main_image)

    iterate_all_pic_dir_img(main_image, draw, PIC_DIR)

    logging.info('Display Image')
    epd.display(epd.getbuffer(main_image))
    logging.info('Displaying Image Success')
    epd.sleep()


if __name__ == '__main__':
    main()

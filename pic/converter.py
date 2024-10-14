import cairosvg
from PIL import Image, ImageOps
import io
import os


def svg_to_bmp(svg_file_path, bmp_file_path, scale=1):
    # Convert SVG to PNG in memory
    png_data = cairosvg.svg2png(url=svg_file_path, scale=scale)

    # Ensure png_data is of type bytes
    if not isinstance(png_data, bytes):
        raise TypeError("Expected png_data to be of type bytes")

    # Open the PNG image from the in-memory data
    image = Image.open(io.BytesIO(png_data))

    # Convert the image to grayscale
    grayscale_image = image.convert("1")  # 'L' for grayscale
    img_inverted = ImageOps.invert(grayscale_image)
    # Apply a threshold to convert to 1-bit black and white
    # Any pixel value less than 255 (white) becomes black
    # bw_image = grayscale_image.point(lambda x: 255 if x < 255 else 0, "1")

    # Convert and save the image as BMP
    img_inverted.save(bmp_file_path, format="BMP")


def convert_all_svgs_in_directory(directory_path, scale=1):
    # Iterate over all files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".svg"):
            svg_file_path = os.path.join(directory_path, filename)
            bmp_file_path = os.path.join(
                directory_path, f"{os.path.splitext(filename)[0]}.bmp"
            )

            # Convert each SVG to BMP
            svg_to_bmp(svg_file_path, bmp_file_path, scale)
            print(f"Converted {svg_file_path} to {bmp_file_path}")


# Example usage
directory = "."
convert_all_svgs_in_directory(directory, scale=2)  # Adjust scale for higher resolution

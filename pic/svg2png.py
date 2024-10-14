import cairosvg
from PIL import Image, ImageOps
import io
import os


def svg_to_png_1bit(svg_file_path, png_file_path, scale=1):
    # Convert SVG to PNG in memory
    png_data = cairosvg.svg2png(url=svg_file_path, scale=scale)

    # Ensure png_data is of type bytes
    if not isinstance(png_data, bytes):
        raise TypeError("Expected png_data to be of type bytes")

    # Open the PNG image from the in-memory data
    image = Image.open(io.BytesIO(png_data))

    # Convert the image to grayscale
    grayscale_image = image.convert("L")  # 'L' for grayscale

    img_inverted = ImageOps.invert(grayscale_image)

    # Apply a threshold to convert to 1-bit black and white
    # Any pixel value less than 255 (white) becomes black
    bw_image = img_inverted.point(lambda x: 0 if x < 255 else 255, "1")

    # Save the image as PNG
    bw_image.save(png_file_path, format="PNG")


def convert_all_svgs_in_directory_to_png(directory_path, scale=1):
    # Iterate over all files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".svg"):
            svg_file_path = os.path.join(directory_path, filename)
            png_file_path = os.path.join(
                directory_path, f"{os.path.splitext(filename)[0]}.png"
            )

            # Convert each SVG to PNG
            svg_to_png_1bit(svg_file_path, png_file_path, scale)
            print(f"Converted {svg_file_path} to {png_file_path}")


# Example usage
directory = "."
convert_all_svgs_in_directory_to_png(
    directory, scale=2
)  # Adjust scale for higher resolution

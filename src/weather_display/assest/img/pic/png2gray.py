from PIL import Image, ImageOps
import os


def convert_and_save_png_to_grayscale(input_file_path, output_directory):
    # Open the color image
    with Image.open(input_file_path) as image:
        # Convert the image to grayscale
        grayscale_image = image.convert("L")  # 'L' for grayscale

        img_inverted = ImageOps.invert(grayscale_image)

        # Apply a threshold to convert to 1-bit black and white
        # Any pixel value less than 255 (white) becomes black
        bw_image = img_inverted.point(lambda x: 0 if x < 255 else 255, "1")
        resized_image = bw_image.resize((200, 200))

        # Save the original grayscale image
        original_output_path = os.path.join(
            output_directory, f"md_{os.path.basename(input_file_path)}"
        )
        bw_image.save(original_output_path, format="PNG")
        print(f"Saved original grayscale image: {original_output_path}")

        # Resize the image to the specified size
        resized_image = bw_image.resize((96, 96))

        # Save the resized grayscale image
        resized_output_path = os.path.join(
            output_directory, f"sm_{os.path.basename(input_file_path)}"
        )
        resized_image.save(resized_output_path, format="PNG")
        print(f"Saved resized grayscale image: {resized_output_path}")


def convert_all_pngs_in_directory(directory_path, output_directory):
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Iterate over all files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".png"):
            input_file_path = os.path.join(directory_path, filename)

            # Convert and save each PNG to grayscale and resized versions
            convert_and_save_png_to_grayscale(input_file_path, output_directory)


# Example usage
input_directory = "."
output_directory = "./monochrome"
convert_all_pngs_in_directory(input_directory, output_directory)

import cv2
import numpy as np
from PIL import Image
from modules import scripts_postprocessing
import gradio as gr
from modules.ui_components import FormRow, FormColumn, FormGroup, ToolButton, FormHTML

mode_dict = {"Nearest": Image.NEAREST,
             "Bicubic": Image.BICUBIC,
             "Bilinear": Image.BILINEAR,
             "Hamming": Image.HAMMING,
             "Lanczos": Image.LANCZOS}


def downscale_image(img, scale, mode):
    width, height = img.size
    img = img.resize(
        (int(width / scale), int(height / scale)), mode_dict[str(mode)])
    return img


def palette_limit(img, palette_size=16):
    if palette_size > 1:
        img = img.quantize(colors=palette_size, dither=None)
    return img


def rescale_image(img, original_size):
    width, height = original_size
    # rescale the image
    scaled_img = img.resize((width, height), Image.NEAREST)
    return scaled_img


def grayscalelimit(img, graylimit=155):
    # Convert the image to grayscale
    img_gray = img.convert('L')

    # Create a new image with the same size as the grayscale image, filled with white color
    img_bw = Image.new('L', img_gray.size, color=255)

    # Get the pixel access object for both images
    pixels_gray = img_gray.load()
    pixels_bw = img_bw.load()

    # Loop through each pixel in the grayscale image
    for x in range(img_gray.width):
        for y in range(img_gray.height):
            # If the grayscale pixel is less than or equal to 128,
            # set the corresponding pixel in the black and white image to black
            if pixels_gray[x, y] <= graylimit:
                pixels_bw[x, y] = 0

    return img_bw


class ScriptPostprocessingUpscale(scripts_postprocessing.ScriptPostprocessing):
    name = "pixel"
    order = 20000
    model = None

    def ui(self):
        with FormGroup():
            # Pixelate and rescale
            with FormRow():
                # Enable or disable pixelation
                pixelate_cb = gr.Checkbox(label="Pixelate", value=False)

                # Enable or disable rescaling
                rescale = gr.Checkbox(label="Rescale", value=False)

            # Downscale
            with FormRow(visible=False) as downscale_row:
                # Adjust the downscaling factor
                downscale = gr.Slider(label="Downscale", minimum=1, maximum=32, step=1, value=8)
                # Select downscaling mode
                mode = gr.Dropdown(label="Mode", choices=list(mode_dict.keys()), value=list(mode_dict.keys())[0], multiselect=False)

            # Palette
            with FormRow():
                # Enable or disable palette limit
                palette_limit_cb = gr.Checkbox(label="Color Palette Limit", value=False)
            with FormRow(visible=False) as palette_row:
                # Adjust the palette size
                palette_size = gr.Slider(label="Palette Size", minimum=0, maximum=256, step=1, value=1)

            # Graylimit
            with FormRow():
                # Enable or disable gray thresholding
                gray_threshold_cb = gr.Checkbox(label="Gray Thresholding", value=False)
                with FormRow(visible=False) as gray_threshold_row:
                    # Adjust the graylimit value
                    gray_threshold = gr.Slider(label="Threshold", minimum=0, maximum=255, step=1, value=0)

                pixelate_cb.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[pixelate_cb],
                    outputs=[downscale_row],
                )

                palette_limit_cb.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[palette_limit_cb],
                    outputs=[palette_row],
                )

                gray_threshold_cb.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[gray_threshold_cb],
                    outputs=[gray_threshold_row],
                )

            return {
                "pixelate_cb": pixelate_cb,
                "rescale": rescale,
                "downscale": downscale,
                "mode": mode,

                "palette_limit_cb": palette_limit_cb,
                "palette_size": palette_size,

                "gray_limit_cb": gray_threshold_cb,
                "graylimit": gray_threshold,
            }

    def process(self, pp: scripts_postprocessing.PostprocessedImage, pixelate_cb, rescale, downscale, mode,
                palette_limit_cb,
                palette_size, gray_limit_cb, graylimit):

        # if image is not RGBA, convert it to RGBA
        if pp.image.mode != 'RGBA':
            img = pp.image.convert('RGBA')
        else:
            img = pp.image

        original_size = img.size
        applied_effects = ""

        if pixelate_cb and downscale > 1:
            img = downscale_image(img, downscale, mode)
            applied_effects += f"Downscale: {downscale}, Mode: {mode}, "

        if palette_limit_cb and palette_size > 1:
            img = palette_limit(img, palette_size)
            applied_effects += f"Color Palette Limit: {palette_size}, "

        if gray_limit_cb and graylimit > 0:
            img = grayscalelimit(img, graylimit)
            applied_effects += f"Gray Limit: {graylimit}, "

        # Pass the original size and the image to the rescale_image function
        if rescale and pixelate_cb:
            img = rescale_image(img, original_size)
            applied_effects += f"rescale, "

        # Convert back to original mode
        pp.image = img.convert(pp.image.mode)

        # Send debug message if effects applied
        if len(applied_effects) > 2:
            print(f"Pixelate with {applied_effects[:-2]}")

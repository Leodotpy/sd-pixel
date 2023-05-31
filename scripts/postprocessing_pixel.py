import cv2
import numpy as np
from PIL import Image
from modules import scripts_postprocessing
import gradio as gr
from modules.ui_components import FormRow, FormColumn, FormGroup, ToolButton, FormHTML


def downscale_image(img, scale):
    width, height = img.size
    img = img.resize(
        (int(width / scale), int(height / scale)), Image.NEAREST)
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
            # If the grayscale pixel is less than or equal to 128, set the corresponding pixel in the black and white image to black
            if pixels_gray[x, y] <= graylimit:
                pixels_bw[x, y] = 0

    return img_bw


class ScriptPostprocessingUpscale(scripts_postprocessing.ScriptPostprocessing):
    name = "pixel"
    order = 20000
    model = None

    def on_pixelate_change(self, value):
        self.downscale.enabled = value
        self.palette_size.enabled = value
        self.graylimit.enabled = value
        self.rescale.enabled = value

    def on_palette_size_change(self, value):
        if value > 0:
            self.palette_size.enabled = value
        else:
            self.palette_size.enabled = False

    def on_graylimit_change(self, value):
        self.graylimit.enabled = value

    def ui(self):
        with FormGroup():
            # Pixelate and rescale
            with FormRow():
                pixelate_cb = gr.Checkbox(label="Pixelate", value=False, on_change=self.on_pixelate_change,
                                          hover_text="Enable or disable pixelation.")

                self.rescale = gr.Checkbox(label="Rescale", value=False, enabled=False,
                                           hover_text="Enable or disable rescaling.")

            with FormRow(visible=False) as downscale_row:
                self.downscale = gr.Slider(label="Downscale", minimum=1, maximum=32, step=1, value=8, enabled=True,
                                           hover_text="Adjust the downscaling factor.")
            # Palette
            with FormRow():
                palette_limit_cb = gr.Checkbox(label="Color Palette Limit", value=False,
                                               on_change=self.on_pixelate_change,
                                               hover_text="Enable or disable palette limit.")
            with FormRow(visible=False) as palette_row:
                self.palette_size = gr.Slider(label="Palette Size", minimum=0, maximum=256, step=1, value=1,
                                              enabled=True,
                                              on_change=self.on_palette_size_change,
                                              hover_text="Adjust the palette size.")

            # Graylimit
            with FormRow():
                gray_limit_cb = gr.Checkbox(label="Gray Limit", value=False, on_change=self.on_pixelate_change,
                                            hover_text="Enable or disable palette limit.")
                with FormRow(visible=False) as graylimit_row:
                    self.graylimit = gr.Slider(label="Graylimit", minimum=0, maximum=255, step=1, value=0, enabled=True,
                                               on_change=self.on_graylimit_change,
                                               hover_text="Adjust the graylimit value.")

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

                gray_limit_cb.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[gray_limit_cb],
                    outputs=[graylimit_row],
                )

            return {
                "pixelate_cb": pixelate_cb,
                "rescale": self.rescale,
                "downscale": self.downscale,

                "palette_limit_cb": palette_limit_cb,
                "palette_size": self.palette_size,

                "gray_limit_cb": gray_limit_cb,
                "graylimit": self.graylimit,
            }

    def process(self, pp: scripts_postprocessing.PostprocessedImage, pixelate_cb, rescale, downscale,
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
            img = downscale_image(img, downscale)
            applied_effects += f"Downscale: {downscale}, "

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

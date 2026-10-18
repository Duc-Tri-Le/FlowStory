"""Image Post-processing Filter for Noir Storytime Animation Backgrounds.

Transforms generated background images into moody, low-brightness noir backdrops:
1. Desaturate colors (pure B&W or cold muted tint).
2. Dim brightness (darken by 25-35% so 2D white doodle characters stand out).
3. Boost contrast and add subtle cinematic vignette around edges.
"""
import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ImageEnhance, ImageOps

logger = logging.getLogger(__name__)


def apply_noir_filter(
    input_image_path: str,
    output_image_path: str,
    saturation: float = 0.08,   # 0.0 = pure B&W, 0.08 = subtle cold tint
    brightness: float = 0.70,   # 0.70 = dimmed by 30%
    contrast: float = 1.15,     # 1.15 = slightly punchier shadows
    add_vignette: bool = True,
) -> str:
    """Transform an image into a dark, desaturated noir background.

    Args:
        input_image_path: Path to source image.
        output_image_path: Path to write processed image.
        saturation: Color saturation factor (0.0 to 1.0).
        brightness: Brightness factor (e.g. 0.65 to 0.80).
        contrast: Contrast factor (e.g. 1.0 to 1.3).
        add_vignette: Whether to apply a subtle dark corner vignette.

    Returns:
        Path to the output image file.
    """
    in_path = Path(input_image_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_image_path}")

    out_path = Path(output_image_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(str(in_path)).convert("RGB") as img:
        # 1. Reduce saturation
        if saturation < 1.0:
            color_enhancer = ImageEnhance.Color(img)
            img = color_enhancer.enhance(saturation)

        # 2. Dim brightness
        if brightness != 1.0:
            bright_enhancer = ImageEnhance.Brightness(img)
            img = bright_enhancer.enhance(brightness)

        # 3. Enhance contrast
        if contrast != 1.0:
            contrast_enhancer = ImageEnhance.Contrast(img)
            img = contrast_enhancer.enhance(contrast)

        # 4. Optional Vignette
        if add_vignette:
            # Create a soft radial gradient vignette
            width, height = img.size
            vignette = Image.new("L", (width, height), 0)
            # Create a simple border darkening mask
            from PIL import ImageDraw
            draw = ImageDraw.Draw(vignette)
            # Draw semi-transparent dark borders
            pad_x = int(width * 0.12)
            pad_y = int(height * 0.12)
            draw.rectangle(
                [pad_x, pad_y, width - pad_x, height - pad_y],
                fill=255
            )
            # Blur the mask
            from PIL import ImageFilter
            vignette = vignette.filter(ImageFilter.GaussianBlur(radius=min(pad_x, pad_y)))
            black_bg = Image.new("RGB", (width, height), (10, 10, 15))
            img = Image.composite(img, black_bg, vignette)

        img.save(str(out_path), quality=95)
        logger.info("Saved noir background: %s (sat=%.2f, bright=%.2f)", out_path.name, saturation, brightness)

    return str(out_path)

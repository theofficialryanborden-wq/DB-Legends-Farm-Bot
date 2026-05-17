from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from .config import Point, Region, TemplateConfig


@dataclass(frozen=True)
class Match:
    name: str
    point: Point
    confidence: float


class ScreenAnalyzer:
    def __init__(self, templates: list[TemplateConfig] | None = None) -> None:
        self.templates = {template.name: template for template in templates or []}

    def has_template(self, name: str | None) -> bool:
        return bool(name and name in self.templates)

    def image_from_png(self, payload: bytes):
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("Pillow is required for screenshot analysis") from exc
        return Image.open(BytesIO(payload)).convert("RGB")

    def average_brightness(self, image, region: Region | None) -> float:
        crop = self._crop(image, region)
        pixels = list(crop.getdata())
        if not pixels:
            return 0.0
        return sum((red + green + blue) / 3 for red, green, blue in pixels) / len(pixels)

    def brightest_column_x(self, image, region: Region) -> int | None:
        crop = self._crop(image, region)
        width, height = crop.size
        if width <= 0 or height <= 0:
            return None
        best_x = 0
        best_score = -1.0
        for x in range(width):
            score = 0.0
            for y in range(height):
                red, green, blue = crop.getpixel((x, y))
                score += (red + green + blue) / 3
            if score > best_score:
                best_score = score
                best_x = x
        return region.left + best_x

    def find_template(self, image, name: str) -> Match | None:
        template_config = self.templates.get(name)
        if template_config is None:
            return None
        template = self._load_template(template_config.path)
        search_area = self._crop(image, template_config.region)
        offset_x = template_config.region.left if template_config.region else 0
        offset_y = template_config.region.top if template_config.region else 0
        best = self._best_template_match(search_area, template, template_config.stride)
        if best is None:
            return None
        x, y, confidence = best
        if confidence < template_config.threshold:
            return None
        center = Point(offset_x + x + template.size[0] // 2, offset_y + y + template.size[1] // 2)
        return Match(template_config.name, center, confidence)

    def _load_template(self, path: str):
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("Pillow is required for template matching") from exc
        return Image.open(Path(path)).convert("RGB")

    def _crop(self, image, region: Region | None):
        if region is None:
            return image
        return image.crop((region.left, region.top, region.right, region.bottom))

    def _best_template_match(self, image, template, stride: int) -> tuple[int, int, float] | None:
        width, height = image.size
        template_width, template_height = template.size
        if template_width > width or template_height > height:
            return None
        best: tuple[int, int, float] | None = None
        for y in range(0, height - template_height + 1, stride):
            for x in range(0, width - template_width + 1, stride):
                confidence = self._confidence_at(image, template, x, y)
                if best is None or confidence > best[2]:
                    best = (x, y, confidence)
        return best

    def _confidence_at(self, image, template, x: int, y: int) -> float:
        diff = 0
        count = 0
        for ty in range(template.size[1]):
            for tx in range(template.size[0]):
                red, green, blue = image.getpixel((x + tx, y + ty))
                tred, tgreen, tblue = template.getpixel((tx, ty))
                diff += abs(red - tred) + abs(green - tgreen) + abs(blue - tblue)
                count += 3
        return 1.0 - (diff / (count * 255))

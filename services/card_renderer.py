"""Pillow card renderer for high-fidelity R-plugin visual outputs.

The original R plugin renders HTML/CSS through Puppeteer. AstrBot deployments may
not ship a browser, so this module reproduces the same dark-card visual language
with Pillow while keeping the copied HTML/CSS resources for traceability.
"""

from __future__ import annotations

import hashlib
import io
import math
import textwrap
import urllib.request
from pathlib import Path
from typing import Any

try:  # Pillow is declared in requirements.txt.
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = ImageDraw = ImageFont = None  # type: ignore

ACCENT = "#FFBD73"
BG = "#444444"
PANEL = "#222222"
ITEM = "#2b2b2b"
TEXT = "#ffffff"
SUB = "#c8c8c8"
GOLD = "#ffd700"


def _hash_payload(*parts: Any) -> str:
    h = hashlib.sha1()
    for part in parts:
        h.update(repr(part).encode("utf-8", errors="ignore"))
    return h.hexdigest()[:16]


class CardRenderer:
    def __init__(self, resources_dir: Path, output_dir: Path | None = None):
        self.resources_dir = resources_dir
        self.output_dir = output_dir or resources_dir.parent / "data" / "rendered"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.font_fzb = resources_dir / "font" / "FZB.ttf"
        self.font_number = resources_dir / "font" / "江城月湖体 400W.ttf"

    def available(self) -> bool:
        return Image is not None and ImageDraw is not None and ImageFont is not None

    def _font(self, size: int, *, number: bool = False, bold: bool = False):
        if ImageFont is None:
            return None
        candidates = []
        if number:
            candidates.append(self.font_number)
        candidates.append(self.font_fzb)
        candidates.extend([
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        ])
        for path in candidates:
            try:
                if path.exists():
                    return ImageFont.truetype(str(path), size=size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _text_size(self, draw, text: str, font) -> tuple[int, int]:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _wrap(self, text: str, max_chars: int) -> list[str]:
        lines: list[str] = []
        for raw in str(text).splitlines() or [""]:
            if not raw:
                lines.append("")
            else:
                lines.extend(textwrap.wrap(raw, width=max_chars, replace_whitespace=False, drop_whitespace=True) or [raw])
        return lines

    def _rounded(self, draw, xy, radius: int, fill: str, outline: str | None = None, width: int = 1):
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

    def _paste_icon(self, canvas, icon_name: str, box: tuple[int, int, int, int]):
        icon_path = self.resources_dir / "img" / "icon" / f"{icon_name}.png"
        if not icon_path.exists():
            icon_path = self.resources_dir / "img" / "rank" / "logo.png"
        try:
            icon = Image.open(icon_path).convert("RGBA").resize((box[2] - box[0], box[3] - box[1]))
            canvas.alpha_composite(icon, (box[0], box[1]))
        except Exception:
            pass

    def render_help(self, groups: list[dict[str, Any]], version: str = "1.14.5.14") -> str:
        if not self.available():
            raise RuntimeError("Pillow unavailable")
        path = self.output_dir / f"help_{_hash_payload(groups, version)}.png"
        if path.exists():
            return str(path)

        width = 1182  # original 788px scaled by 1.5
        pad = 24
        head_h = 140
        item_w = (width - pad * 2 - 50 - 24) // 2
        item_h = 96
        group_heights = []
        for group in groups:
            count = len(group.get("list", []))
            rows = max(1, math.ceil(count / 2))
            group_heights.append(70 + rows * (item_h + 24) + 20)
        height = pad + head_h + 24 + sum(group_heights) + 78

        im = Image.new("RGBA", (width, height), BG)
        draw = ImageDraw.Draw(im)
        title_font = self._font(48)
        sub_font = self._font(30)
        group_font = self._font(24)
        item_font = self._font(25)
        desc_font = self._font(20)
        footer_font = self._font(22)

        x0, y = pad, pad
        self._rounded(draw, (x0, y, width - pad, y + head_h), 22, "#333333", ACCENT, 3)
        draw.text((width // 2, y + 28), "R-Plugin", fill=ACCENT, font=title_font, anchor="ma")
        draw.text((width // 2, y + 88), f"Ver：v{version}", fill=ACCENT, font=sub_font, anchor="ma")
        logo = self.resources_dir / "img" / "rank" / "logo.png"
        try:
            icon = Image.open(logo).convert("RGBA").resize((88, 88))
            im.alpha_composite(icon, (x0 + 26, y + 24))
        except Exception:
            pass
        y += head_h + 36

        for idx, group in enumerate(groups):
            gh = group_heights[idx]
            self._rounded(draw, (x0, y, width - pad, y + gh), 22, PANEL)
            self._rounded(draw, (x0 - 6, y - 16, x0 + 260, y + 38), 18, "#444444")
            draw.text((x0 + 20, y - 8), str(group.get("group", "功能")), fill=TEXT, font=group_font)
            items = group.get("list", [])
            for i, item in enumerate(items):
                col = i % 2
                row = i // 2
                ix = x0 + 25 + col * (item_w + 24)
                iy = y + 60 + row * (item_h + 24)
                self._rounded(draw, (ix, iy, ix + item_w, iy + item_h), 16, ITEM)
                self._paste_icon(im, str(item.get("icon", "update")), (ix + 18, iy + 24, ix + 62, iy + 68))
                title = str(item.get("title", ""))
                desc = str(item.get("desc", ""))
                draw.text((ix + 82, iy + 17), title[:30], fill=TEXT, font=item_font)
                draw.text((ix + 82, iy + 54), desc[:42], fill=(210, 210, 210, 210), font=desc_font)
            y += gh + 24
        draw.text((width // 2, height - 42), "Created By Yunzai-Bot & R-Plugin", fill="#e1d7b7", font=footer_font, anchor="ma")
        im.convert("RGB").save(path, quality=95)
        return str(path)

    def render_version(self, version: str, items: list[str]) -> str:
        if not self.available():
            raise RuntimeError("Pillow unavailable")
        path = self.output_dir / f"version_{_hash_payload(version, items)}.png"
        if path.exists():
            return str(path)

        width = 804  # original 536px scaled by 1.5
        lines: list[str] = []
        for item in items:
            lines.extend(self._wrap(item, 31))
        height = 60 + 96 + max(260, len(lines) * 34 + 70) + 72
        im = Image.new("RGBA", (width, height), "#1e1e1e")
        draw = ImageDraw.Draw(im)
        title_font = self._font(34)
        item_font = self._font(24)
        footer_font = self._font(20)
        x, y = 30, 30
        self._rounded(draw, (x, y, width - x, height - 80), 16, "#3a3a3a")
        draw.rounded_rectangle((x, y, width - x, y + 82), radius=16, fill="#2b2b2b")
        draw.text((x + 28, y + 23), f"R插件版本：v{version}", fill=ACCENT, font=title_font)
        cy = y + 110
        for item in items:
            wrapped = self._wrap(item, 31)
            if not wrapped:
                continue
            draw.text((x + 38, cy), "•", fill=ACCENT, font=item_font)
            draw.text((x + 70, cy), wrapped[0], fill="#f0f0f0", font=item_font)
            cy += 34
            for cont in wrapped[1:]:
                draw.text((x + 70, cy), cont, fill="#f0f0f0", font=item_font)
                cy += 34
            cy += 4
        draw.line((x + 20, height - 78, width - x - 20, height - 78), fill="#555555", width=1)
        draw.text((width // 2, height - 50), "Created By Yunzai-Bot & R-Plugin", fill="#e1d7b7", font=footer_font, anchor="ma")
        im.convert("RGB").save(path, quality=95)
        return str(path)

    def _load_cover(self, cover: str, size: tuple[int, int]):
        if Image is None:
            return None
        try:
            if cover.startswith("http://") or cover.startswith("https://"):
                req = urllib.request.Request(cover, headers={"User-Agent": "Mozilla/5.0 AstrBot-RConsole"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read(2 * 1024 * 1024)
                return Image.open(io.BytesIO(raw)).convert("RGBA").resize(size)
            if cover:
                return Image.open(cover).convert("RGBA").resize(size)
        except Exception:
            return None
        return None

    def render_pick_song(self, songs: list[dict[str, Any]]) -> str:
        if not self.available():
            raise RuntimeError("Pillow unavailable")
        path = self.output_dir / f"pick_song_{_hash_payload(songs)}.png"
        if path.exists():
            return str(path)

        width = 1000
        row_h = 126
        height = 36 + max(1, len(songs)) * row_h + 78
        im = Image.new("RGBA", (width, height), "#121212")
        draw = ImageDraw.Draw(im)
        num_font = self._font(52, number=True)
        name_font = self._font(38)
        singer_font = self._font(28)
        dur_font = self._font(28)
        tag_font = self._font(22)
        footer_font = self._font(22, number=True)

        # watermark logo
        try:
            icon = Image.open(self.resources_dir / "img" / "icon" / "neteaseRank.png").convert("RGBA").resize((230, 230))
            icon.putalpha(90)
            im.alpha_composite(icon, (width // 2 - 115, height // 2 - 115))
        except Exception:
            pass

        y = 30
        for idx, song in enumerate(songs, 1):
            draw.text((40, y + 34), str(idx), fill=TEXT, font=num_font)
            cover_box = (108, y + 16, 198, y + 106)
            cover = str(song.get("cover") or "")
            pasted = False
            cover_img = self._load_cover(cover, (90, 90))
            if cover_img is not None:
                im.alpha_composite(cover_img, (cover_box[0], cover_box[1]))
                pasted = True
            if not pasted:
                try:
                    img = Image.open(self.resources_dir / "img" / "default.png").convert("RGBA").resize((90, 90))
                    im.alpha_composite(img, (cover_box[0], cover_box[1]))
                except Exception:
                    self._rounded(draw, cover_box, 10, "#303030")
            draw.text((220, y + 24), str(song.get("songName", "未知歌曲"))[:22], fill=TEXT, font=name_font)
            draw.text((220, y + 70), str(song.get("singerName", "未知歌手"))[:30], fill="#aaaaaa", font=singer_font)
            tag = song.get("type")
            dx = width - 130
            if tag in {"cloud", "podcast"}:
                tag_text = "云盘" if tag == "cloud" else "播客"
                color = "#dd001b" if tag == "cloud" else "#7c4dff"
                self._rounded(draw, (dx - 18, y + 20, dx + 62, y + 52), 10, "#121212", color, 2)
                draw.text((dx + 22, y + 24), tag_text, fill=color, font=tag_font, anchor="ma")
                draw.text((dx + 22, y + 64), str(song.get("duration", "00:00")), fill="#aaaaaa", font=dur_font, anchor="ma")
            else:
                draw.text((dx + 22, y + 46), str(song.get("duration", "00:00")), fill="#aaaaaa", font=dur_font, anchor="ma")
            y += row_h
        draw.text((width // 2, height - 46), "Created By Yunzai-Bot & R-Plugin", fill=(255, 255, 255, 175), font=footer_font, anchor="ma")
        im.convert("RGB").save(path, quality=95)
        return str(path)

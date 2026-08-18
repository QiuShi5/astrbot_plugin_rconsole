import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT
# Original R-plugin HTML/CSS assets are preserved inside the plugin's resources/.
SRC = ROOT / "resources"

sys.path.insert(0, str(PLUGIN))

from services.help_version import HelpVersionService  # noqa: E402


def read(path):
    return path.read_text(encoding="utf-8")


def assert_contains(text, values, label):
    missing = [v for v in values if v not in text]
    assert not missing, f"{label} missing {missing}"


def render_sample_images(tmp: Path) -> dict[str, list[str]]:
    svc = HelpVersionService(ROOT / "resources", output_dir=tmp)
    help_out = svc.help_text()
    version_out = svc.version_text()
    from services.card_renderer import CardRenderer

    renderer = CardRenderer(ROOT / "resources", output_dir=tmp)
    fixture_songs = [
        {"songName": "晴天", "singerName": "周杰伦", "duration": "04:29", "type": "song", "cover": ""},
        {"songName": "告白气球", "singerName": "周杰伦", "duration": "03:35", "type": "song", "cover": ""},
        {"songName": "稻香", "singerName": "周杰伦", "duration": "03:43", "type": "song", "cover": ""},
    ]
    pick_path = renderer.render_pick_song(fixture_songs)
    return {"help": help_out.images, "version": version_out.images, "pick_song": [pick_path]}


def main():
    help_css = read(SRC / "html/help/help.css")
    version_css = read(SRC / "html/version/version.css")
    pick_css = read(SRC / "html/pick-song/pick-song.css")
    pick_html = read(SRC / "html/pick-song/pick-song.html")
    renderer = read(PLUGIN / "services/card_renderer.py")

    assert_contains(
        help_css, ["width: 788px", "transform: scale(1.5)", "#FFBD73", "FZB.ttf", "calc(50% - 20px)"], "help css"
    )
    assert_contains(version_css, ["width: 536px", "transform: scale(1.5)", "#FFBD73", "#1e1e1e"], "version css")
    assert_contains(pick_css, ["background: #121212ef", "江城月湖体"], "pick css")
    assert_contains(pick_html, ["neteaseRank.png", "Created By Yunzai-Bot & R-Plugin"], "pick html")
    assert_contains(
        renderer,
        [
            "width = 1182",
            "width = 804",
            "width = 1000",
            'ACCENT = "#FFBD73"',
            "FZB.ttf",
            "neteaseRank.png",
            "def _load_cover",
            "urllib.request",
        ],
        "renderer",
    )

    with tempfile.TemporaryDirectory(prefix="rconsole_style_") as tmp_str:
        tmp = Path(tmp_str)
        images = render_sample_images(tmp)
        assert images["help"], "help image not rendered"
        assert images["version"], "version image not rendered"
        assert images["pick_song"], "pick_song image not rendered"
        sizes = {name: Image.open(paths[0]).size for name, paths in images.items()}
        assert sizes["help"][0] == 1182, sizes
        assert sizes["version"][0] == 804, sizes
        assert sizes["pick_song"][0] == 1000, sizes

        expected = {
            "help_original_width": 788,
            "help_scale": 1.5,
            "help_render_width": 1182,
            "version_original_width": 536,
            "version_scale": 1.5,
            "version_render_width": 804,
            "pick_song_dark_background": "#121212",
            "accent_color": "#FFBD73",
            "font": "FZB.ttf",
            "icons_preserved_count": len(list((PLUGIN / "resources/img/icon").glob("*.png"))),
            "rendered_sizes": {k: list(v) for k, v in sizes.items()},
        }
        out = ROOT / "docs/style_quantitative_check.json"
        out.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
        print("style quantitative checks ok")
        print(json.dumps(expected, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

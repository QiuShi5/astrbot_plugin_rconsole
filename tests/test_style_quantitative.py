import json
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / 'astrbot_plugin_rconsole'
SRC = ROOT / 'source' / 'rconsole-plugin'


def read(path):
    return path.read_text(encoding='utf-8')


def assert_contains(text, values, label):
    missing = [v for v in values if v not in text]
    assert not missing, f'{label} missing {missing}'


def main():
    help_css = read(SRC / 'resources/html/help/help.css')
    version_css = read(SRC / 'resources/html/version/version.css')
    pick_css = read(SRC / 'resources/html/pick-song/pick-song.css')
    pick_html = read(SRC / 'resources/html/pick-song/pick-song.html')
    renderer = read(PLUGIN / 'services/card_renderer.py')

    assert_contains(help_css, ['width: 788px', 'transform: scale(1.5)', '#FFBD73', 'FZB.ttf', 'calc(50% - 20px)'], 'help css')
    assert_contains(version_css, ['width: 536px', 'transform: scale(1.5)', '#FFBD73', '#1e1e1e'], 'version css')
    assert_contains(pick_css, ['background: #121212ef', '江城月湖体'], 'pick css')
    assert_contains(pick_html, ['neteaseRank.png', 'Created By Yunzai-Bot & R-Plugin'], 'pick html')
    assert_contains(renderer, ['width = 1182', 'width = 804', 'width = 1000', 'ACCENT = "#FFBD73"', 'FZB.ttf', 'neteaseRank.png', 'def _load_cover', 'urllib.request'], 'renderer')

    images = {
        'help': next((PLUGIN / 'data/rendered').glob('help_*.png')),
        'version': next((PLUGIN / 'data/rendered').glob('version_*.png')),
        'pick_song': next((PLUGIN / 'data/rendered').glob('pick_song_*.png')),
    }
    sizes = {name: Image.open(path).size for name, path in images.items()}
    assert sizes['help'][0] == 1182, sizes
    assert sizes['version'][0] == 804, sizes
    assert sizes['pick_song'][0] == 1000, sizes

    expected = {
        'help_original_width': 788,
        'help_scale': 1.5,
        'help_render_width': 1182,
        'version_original_width': 536,
        'version_scale': 1.5,
        'version_render_width': 804,
        'pick_song_dark_background': '#121212',
        'accent_color': '#FFBD73',
        'font': 'FZB.ttf',
        'icons_preserved_count': len(list((PLUGIN / 'resources/img/icon').glob('*.png'))),
        'rendered_sizes': {k: list(v) for k, v in sizes.items()},
    }
    out = ROOT / 'docs/style_quantitative_check.json'
    out.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding='utf-8')
    print('style quantitative checks ok')
    print(json.dumps(expected, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

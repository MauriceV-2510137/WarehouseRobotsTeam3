"""
Render all .puml files in this directory to PNG via the PlantUML public server.
Usage: python docs/UML/render.py
"""
import sys, zlib, urllib.request, pathlib

sys.stdout.reconfigure(encoding='utf-8')

UML_DIR = pathlib.Path(__file__).parent


def _6bit(b):
    if b < 10:  return chr(48 + b)
    b -= 10
    if b < 26:  return chr(65 + b)
    b -= 26
    if b < 26:  return chr(97 + b)
    b -= 26
    if b == 0:  return '-'
    if b == 1:  return '_'
    return '?'


def _append3(b1, b2, b3):
    return (
        _6bit(b1 >> 2) +
        _6bit(((b1 & 3) << 4) | (b2 >> 4)) +
        _6bit(((b2 & 0xF) << 2) | (b3 >> 6)) +
        _6bit(b3 & 0x3F)
    )


def plantuml_encode(text: str) -> str:
    raw = zlib.compress(text.encode('utf-8'), 9)[2:-4]   # strip zlib header/checksum → deflate
    out = []
    for i in range(0, len(raw) - 2, 3):
        out.append(_append3(raw[i], raw[i+1], raw[i+2]))
    r = len(raw) % 3
    if r == 1:
        out.append(_append3(raw[-1], 0, 0)[:2])
    elif r == 2:
        out.append(_append3(raw[-2], raw[-1], 0)[:3])
    return ''.join(out)


for puml in sorted(UML_DIR.glob('*.puml')):
    text = puml.read_text(encoding='utf-8')
    encoded = plantuml_encode(text)
    url = f'https://www.plantuml.com/plantuml/png/{encoded}'
    out = puml.with_suffix('.png')
    print(f'Rendering {puml.name} ...', end=' ', flush=True)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            out.write_bytes(resp.read())
        print(f'→ {out.name}')
    except Exception as e:
        print(f'FAILED: {e}')

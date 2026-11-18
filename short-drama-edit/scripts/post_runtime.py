"""Local execution primitives: content-addressed stages and cue-preserving ASS.

No editorial selection lives here. The Markdown edit remains the decision source.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.pending')
    pending.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    pending.replace(path)


def settings(episode):
    path = Path(episode) / '后期配置.json'
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if value.get('version') != 1:
        raise ValueError('后期配置.json requires version: 1')
    if value.get('subtitle_timing', 'exact') not in {'exact', 'legacy'}:
        raise ValueError('subtitle_timing: exact or legacy')
    return value


class StageCache:
    """Reuse only complete outputs for unchanged bytes, parameters and tool build."""

    def __init__(self, root, binary, sources):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        build = subprocess.run([binary, '-version'], capture_output=True, check=True).stdout
        self.engine = hashlib.sha256(build + b''.join(Path(p).read_bytes() for p in sources)).hexdigest()
        self.events = []

    def run(self, stage, command, inputs, execute):
        output = Path(command[-1])
        identity = {'engine': self.engine, 'args': list(map(str, command[:-1])),
                    'inputs': {str(Path(p).resolve()): digest(p) for p in inputs}}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        receipt = self.root / (stage + '.json')
        previous = json.loads(receipt.read_text()) if receipt.exists() else {}
        begin = time.perf_counter()
        hit = previous.get('key') == key and output.exists() and previous.get('output') == digest(output)
        attempts = 0
        if not hit:
            failures = []
            for attempt in range(2):
                attempts = attempt + 1
                try:
                    execute(command)
                    break
                except Exception as error:
                    failures.append(f'Attempt {attempts}: {error}')
                    (self.root / (stage + '.errors.txt')).write_text('\n'.join(failures), encoding='utf-8')
                    transient = any(term in str(error).lower() for term in
                                    ('resource temporarily unavailable', 'device or resource busy', 'being used by another process'))
                    if not transient or attempt:
                        raise
            # A process exit is necessary, but an absent/truncated output is not cacheable.
            if not output.is_file() or output.stat().st_size == 0:
                raise ValueError('Render stage produced no media: ' + stage)
            if any(digest(p) != h for p, h in identity['inputs'].items()):
                raise ValueError('Input changed during render: ' + stage)
            save(receipt, {'key': key, 'output': digest(output)})
        self.events.append({'stage': stage, 'cache_hit': hit, 'attempts': attempts,
                            'seconds': round(time.perf_counter() - begin, 4)})


PALETTES = {
    'cinema': {'font': 'Noto Sans CJK SC', 'size': .036, 'outline': .0018, 'bottom': .17,
               'color': '#F4F1EA', 'accent': '#E4C78E', 'bold': False, 'fade_ms': 0},
    'clear': {'font': 'Noto Sans CJK SC', 'size': .043, 'outline': .003, 'bottom': .21,
              'color': '#FFFFFF', 'accent': '#F0D37B', 'bold': True, 'fade_ms': 0},
    'editorial': {'font': 'Noto Sans CJK SC', 'size': .04, 'outline': .002, 'bottom': .19,
                  'color': '#F7F6F1', 'accent': '#C2D4CC', 'bold': True, 'fade_ms': 70},
}


def color(value):
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        raise ValueError('Subtitle colors use #RRGGBB')
    return '&H00' + value[5:7] + value[3:5] + value[1:3] + '&'


def numeric(value, low, high, label):
    value = float(value)
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{label} must be in {low}..{high}')
    return value


def escaped(text):
    return str(text).replace('\\', '＼').replace('{', '｛').replace('}', '｝').replace('\n', r'\N')


def clock(seconds):
    value = round(seconds * 100)
    return f'{value // 360000}:{value // 6000 % 60:02}:{value // 100 % 60:02}.{value % 100:02}'


def cue_ass(rows, width, height, config):
    """Keep each cue's exact window. Layout never manufactures speech timing."""
    name = config.get('preset', 'cinema')
    if name not in PALETTES:
        raise ValueError('Unknown subtitle preset: ' + str(name))
    theme = {**PALETTES[name], **config}
    font = theme['font']
    if any(c in font for c in ',\r\n'):
        raise ValueError('Invalid subtitle font family')
    size = height * numeric(theme['size'], .015, .12, 'font size fraction')
    outline = height * numeric(theme['outline'], 0, .015, 'outline fraction')
    bottom = height * numeric(theme['bottom'], .03, .45, 'bottom fraction')
    margin = max(12, width * .065)
    header = f'''[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},{size:.2f},{color(theme['color'])},{color(theme['accent'])},&H00181818,&H80000000,{-1 if theme['bold'] else 0},0,0,0,100,100,0,0,1,{outline:.2f},0,2,{margin:.0f},{margin:.0f},{bottom:.0f},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    result = []
    for index, row in enumerate(rows):
        override = {**theme.get('cues', {}).get(str(index + 1), {}), **row.get('style', {})}
        text = row['text']
        tags = ''
        if 'x' in override or 'y' in override:
            x = numeric(override.get('x', .5), 0, 1, 'cue x') * width
            y = numeric(override.get('y', 1 - theme['bottom']), 0, 1, 'cue y') * height
            tags += f'{{\\an2\\pos({x:.1f},{y:.1f})}}'
        fade = numeric(override.get('fade_ms', theme['fade_ms']), 0, 500, 'cue fade')
        fade = min(fade, (row['end'] - row['start']) * 250)
        if fade:
            tags += f'{{\\fad({fade:.0f},{fade:.0f})}}'
        # Explicit line breaks or smart ASS wrapping share the SAME cue interval.
        words = sorted({w for w in row.get('keys', []) if w and w in text}, key=len, reverse=True)
        shown = ''
        cursor = 0
        for match in re.finditer('|'.join(re.escape(w) for w in words), text) if words else []:
            shown += escaped(text[cursor:match.start()])
            shown += '{\\c' + color(theme['accent']) + '}' + escaped(match.group()) + '{\\c' + color(theme['color']) + '}'
            cursor = match.end()
        shown += escaped(text[cursor:])
        result.append(f'Dialogue: 0,{clock(row["start"])},{clock(row["end"])},Main,,0,0,0,,{tags}{shown}')
    return header + '\n'.join(result) + '\n'


def serialize_cues(cues):
    return [{'start': c.start, 'end': c.end, 'text': c.text, 'keys': list(c.keys), 'kind': c.kind} for c in cues]

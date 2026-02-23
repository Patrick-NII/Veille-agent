from __future__ import annotations

import random
import struct
import zlib
from datetime import datetime
from pathlib import Path

BASE_WIDTH = 520
BASE_HEIGHT = 200


def generate_simple_diagram(mode: str, data: dict) -> Path | None:
    width = 1040
    height = 400
    canvas = _blank_canvas(width, height, (255, 255, 255))

    diagram_type = _select_diagram_type(mode, data.get("preferred_type"))
    data["diagram_type"] = diagram_type

    try:
        if diagram_type == "workflow_avant_apres":
            _diagram_architecture_blocks(canvas)
        elif diagram_type == "boucle_feedback":
            _diagram_feedback_loop(canvas)
        elif diagram_type == "roi_simple":
            _diagram_roi_waterfall(canvas)
        else:
            _diagram_constraint_bottleneck(canvas)

        out_dir = Path(data.get("out_dir", "outbox"))
        out_dir.mkdir(parents=True, exist_ok=True)
        output = out_dir / f"visual_{mode}_{diagram_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.png"
        _write_png(output, canvas)
        return output
    except Exception:
        return None


def diagram_caption(diagram_type: str) -> str:
    captions = {
        "workflow_avant_apres": "Workflow avant / après",
        "boucle_feedback": "Boucle de feedback",
        "roi_simple": "ROI simplifié",
        "goulot_contrainte": "Goulot de contrainte",
    }
    return captions.get(diagram_type, "Schéma de décision")


def _select_diagram_type(mode: str, preferred_type: str | None = None) -> str:
    allowed = {"workflow_avant_apres", "boucle_feedback", "roi_simple", "goulot_contrainte"}
    if preferred_type in allowed:
        return preferred_type
    if mode == "daily":
        return random.choice(["workflow_avant_apres", "boucle_feedback"])
    return random.choice(["roi_simple", "goulot_contrainte"])


def mini_diagram_text(diagram_type: str, company: str, decision_type: str) -> str:
    if diagram_type == "workflow_avant_apres":
        return (
            "AVANT  : Validation tardive -> Retours multiples -> Décision lente\n"
            "APRES  : Gate explicite -> Validation unique -> Décision traçable\n"
            f"ANCRE  : {company} / {decision_type}"
        )
    if diagram_type == "boucle_feedback":
        return (
            "Signal terrain -> Ajustement modèle -> Règle métier -> Exécution\n"
            "           ^-------------------------------------------|\n"
            f"ANCRE : boucle active chez {company}"
        )
    if diagram_type == "roi_simple":
        return (
            "Valeur captée\n"
            "  ^\n"
            "  |      /------ gains validés\n"
            "  |_____/------- coûts maîtrisés\n"
            f"ANCRE : arbitrage ROI de {company}"
        )
    return (
        "Flux A ======\\\n"
        "              >=== GOULOT ===> Décision\n"
        "Flux B ======/\n"
        f"ANCRE : contrainte clé pour {company}"
    )


def _blank_canvas(width: int, height: int, color: tuple[int, int, int]) -> list[list[list[int]]]:
    return [[[color[0], color[1], color[2]] for _ in range(width)] for _ in range(height)]


def _draw_rect(
    canvas: list[list[list[int]]],
    x: int,
    y: int,
    w: int,
    h: int,
    fill: tuple[int, int, int],
    border: tuple[int, int, int] | None = None,
) -> None:
    height = len(canvas)
    width = len(canvas[0])
    for yy in range(max(0, y), min(height, y + h)):
        for xx in range(max(0, x), min(width, x + w)):
            is_border = border is not None and (yy in {y, y + h - 1} or xx in {x, x + w - 1})
            color = border if is_border and border is not None else fill
            canvas[yy][xx][0] = color[0]
            canvas[yy][xx][1] = color[1]
            canvas[yy][xx][2] = color[2]


def _draw_line(
    canvas: list[list[list[int]]],
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
    thickness: int = 1,
) -> None:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    while True:
        _stamp(canvas, x0, y0, color, thickness)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _stamp(canvas: list[list[list[int]]], x: int, y: int, color: tuple[int, int, int], radius: int) -> None:
    for yy in range(y - radius, y + radius + 1):
        if yy < 0 or yy >= len(canvas):
            continue
        for xx in range(x - radius, x + radius + 1):
            if xx < 0 or xx >= len(canvas[0]):
                continue
            canvas[yy][xx][0] = color[0]
            canvas[yy][xx][1] = color[1]
            canvas[yy][xx][2] = color[2]


def _diagram_architecture_blocks(canvas: list[list[list[int]]]) -> None:
    sx = len(canvas[0]) / BASE_WIDTH
    sy = len(canvas) / BASE_HEIGHT
    x = lambda value: int(value * sx)
    y = lambda value: int(value * sy)

    fill = (243, 247, 252)
    border = (180, 191, 205)
    accent = (60, 84, 111)

    _draw_rect(canvas, x(30), y(36), x(130), y(52), fill, border)
    _draw_rect(canvas, x(195), y(36), x(130), y(52), fill, border)
    _draw_rect(canvas, x(360), y(36), x(130), y(52), fill, border)

    _draw_line(canvas, x(160), y(62), x(195), y(62), accent, 1)
    _draw_line(canvas, x(325), y(62), x(360), y(62), accent, 1)

    _draw_rect(canvas, x(40), y(120), x(210), y(52), (255, 255, 255), border)
    _draw_rect(canvas, x(280), y(120), x(210), y(52), (255, 255, 255), border)


def _diagram_feedback_loop(canvas: list[list[list[int]]]) -> None:
    sx = len(canvas[0]) / BASE_WIDTH
    sy = len(canvas) / BASE_HEIGHT
    x = lambda value: int(value * sx)
    y = lambda value: int(value * sy)

    border = (170, 182, 197)
    fill = (246, 249, 253)
    accent = (66, 90, 120)

    _draw_rect(canvas, x(180), y(30), x(160), y(48), fill, border)
    _draw_rect(canvas, x(340), y(85), x(140), y(48), fill, border)
    _draw_rect(canvas, x(180), y(140), x(160), y(48), fill, border)
    _draw_rect(canvas, x(40), y(85), x(140), y(48), fill, border)

    _draw_line(canvas, x(260), y(78), x(340), y(108), accent, 1)
    _draw_line(canvas, x(340), y(108), x(260), y(140), accent, 1)
    _draw_line(canvas, x(260), y(140), x(180), y(108), accent, 1)
    _draw_line(canvas, x(180), y(108), x(260), y(78), accent, 1)


def _diagram_roi_waterfall(canvas: list[list[list[int]]]) -> None:
    sx = len(canvas[0]) / BASE_WIDTH
    sy = len(canvas) / BASE_HEIGHT
    x = lambda value: int(value * sx)
    y = lambda value: int(value * sy)

    axis = (198, 207, 219)
    palette = [(47, 102, 144), (61, 126, 166), (95, 149, 181), (133, 172, 195)]

    _draw_line(canvas, x(40), y(170), x(500), y(170), axis, 1)
    _draw_line(canvas, x(40), y(24), x(40), y(170), axis, 1)

    bars = [(80, 120, 60), (180, 95, 75), (280, 70, 100), (380, 130, 40)]
    for idx, (bx, by, bh) in enumerate(bars):
        _draw_rect(canvas, int(bx * sx), int(by * sy), int(60 * sx), int(bh * sy), palette[idx], None)


def _diagram_constraint_bottleneck(canvas: list[list[list[int]]]) -> None:
    sx = len(canvas[0]) / BASE_WIDTH
    sy = len(canvas) / BASE_HEIGHT
    x = lambda value: int(value * sx)
    y = lambda value: int(value * sy)

    border = (188, 198, 210)
    shades = [(232, 239, 247), (216, 227, 238), (201, 216, 230), (186, 206, 223)]

    _draw_rect(canvas, x(40), y(40), x(440), y(32), shades[0], border)
    _draw_rect(canvas, x(90), y(82), x(340), y(30), shades[1], border)
    _draw_rect(canvas, x(140), y(122), x(240), y(28), shades[2], border)
    _draw_rect(canvas, x(190), y(160), x(140), y(24), shades[3], border)


def _write_png(path: Path, canvas: list[list[list[int]]]) -> None:
    height = len(canvas)
    width = len(canvas[0]) if height else 0

    raw = bytearray()
    for row in canvas:
        raw.append(0)
        for pixel in row:
            raw.extend(pixel)

    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), level=9)

    content = bytearray()
    content.extend(b"\x89PNG\r\n\x1a\n")
    content.extend(_chunk(b"IHDR", ihdr))
    content.extend(_chunk(b"IDAT", idat))
    content.extend(_chunk(b"IEND", b""))
    path.write_bytes(bytes(content))


def _chunk(tag: bytes, data: bytes) -> bytes:
    length = struct.pack("!I", len(data))
    crc = struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return length + tag + data + crc

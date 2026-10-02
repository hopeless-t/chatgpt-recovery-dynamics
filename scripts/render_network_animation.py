#!/usr/bin/env python3
"""Render the README network/recovery animation.

The GIF is generated from code so the visual remains reviewable and
reproducible. It performs no network I/O and contains no production telemetry.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1200, 500
FPS = 6
SECONDS = 12
FRAMES = FPS * SECONDS

BG = (9, 14, 24)
PANEL = (18, 26, 41)
GRID = (31, 45, 65)
TEXT = (236, 242, 252)
MUTED = (139, 155, 177)
CYAN = (76, 218, 235)
BLUE = (101, 141, 255)
GREEN = (76, 211, 132)
AMBER = (246, 187, 68)
RED = (239, 95, 108)
WHITE = (250, 252, 255)


def pick_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


F_TITLE = pick_font(30, True)
F_LABEL = pick_font(18, True)
F_SMALL = pick_font(14)
F_METRIC = pick_font(17, True)
F_TINY = pick_font(12)


def smooth(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * smooth(t)


def rounded(draw, box, fill, outline=None, radius=16, width=2):
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def glow_dot(img, x, y, color, r=7):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(*color, 18))
    d.ellipse((x - 13, y - 13, x + 13, y + 13), fill=(*color, 42))
    d.ellipse((x - r, y - r, x + r, y + r), fill=(*color, 255))
    img.alpha_composite(layer)


def moving_dot(img, p0, p1, t, color, r=7):
    x = lerp(p0[0], p1[0], t)
    y = lerp(p0[1], p1[1], t)
    glow_dot(img, x, y, color, r)


def translucent_text(img, xy, text, font, color, alpha=255, anchor=None):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, text, font=font, fill=(*color, alpha), anchor=anchor)
    img.alpha_composite(layer)


def draw_base():
    img = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 40):
        draw.line((x, 0, x, H), fill=GRID, width=1)
    for y in range(0, H, 40):
        draw.line((0, y, W, y), fill=GRID, width=1)

    draw.text((42, 26), "Conversation Recovery Dynamics", font=F_TITLE, fill=TEXT)
    draw.text(
        (43, 66),
        "same logical recovery • two traffic behaviors",
        font=F_SMALL,
        fill=MUTED,
    )

    rounded(draw, (38, 104, 1162, 273), PANEL, outline=(52, 66, 89), radius=20)
    rounded(draw, (38, 294, 1162, 463), PANEL, outline=(52, 66, 89), radius=20)

    draw.text((60, 122), "NAIVE RECOVERY", font=F_LABEL, fill=RED)
    draw.text((60, 312), "PROVIDER-FRIENDLY RECOVERY", font=F_LABEL, fill=GREEN)

    nodes = {
        "clients_top": (130, 195),
        "gate_top": (390, 195),
        "server_top": (785, 195),
        "state_top": (1035, 195),
        "clients_bottom": (130, 385),
        "gate_bottom": (390, 385),
        "server_bottom": (785, 385),
        "state_bottom": (1035, 385),
    }

    for key, (x, y) in nodes.items():
        if "clients" in key:
            rounded(
                draw,
                (x - 76, y - 42, x + 76, y + 42),
                (24, 35, 54),
                outline=(74, 91, 119),
                radius=16,
            )
            draw.text((x, y - 8), "Clients", font=F_LABEL, fill=WHITE, anchor="mm")
            draw.text((x, y + 18), "tabs / windows", font=F_TINY, fill=MUTED, anchor="mm")

        elif "gate" in key:
            color = RED if "top" in key else CYAN
            rounded(
                draw,
                (x - 88, y - 42, x + 88, y + 42),
                (24, 35, 54),
                outline=color,
                radius=16,
            )
            title = "Retry loop" if "top" in key else "Single-flight"
            subtitle = "per context" if "top" in key else "one owner"
            draw.text((x, y - 8), title, font=F_LABEL, fill=WHITE, anchor="mm")
            draw.text((x, y + 18), subtitle, font=F_TINY, fill=MUTED, anchor="mm")

        elif "server" in key:
            rounded(
                draw,
                (x - 98, y - 48, x + 98, y + 48),
                (23, 33, 50),
                outline=(76, 96, 128),
                radius=20,
            )
            draw.text((x, y - 9), "Conversation service", font=F_LABEL, fill=WHITE, anchor="mm")
            draw.text((x, y + 18), "observe / snapshot", font=F_TINY, fill=MUTED, anchor="mm")

        else:
            color = AMBER if "top" in key else GREEN
            rounded(
                draw,
                (x - 76, y - 42, x + 76, y + 42),
                (24, 35, 54),
                outline=color,
                radius=16,
            )
            draw.text((x, y - 8), "Recovery state", font=F_LABEL, fill=WHITE, anchor="mm")
            draw.text((x, y + 18), "B → E → H", font=F_TINY, fill=MUTED, anchor="mm")

    for y in (195, 385):
        draw.line((207, y, 301, y), fill=(69, 84, 109), width=4)
        draw.line((479, y, 686, y), fill=(69, 84, 109), width=4)
        draw.line((884, y, 958, y), fill=(69, 84, 109), width=4)

    draw.text((583, 177), "network", font=F_TINY, fill=MUTED, anchor="mm")
    draw.text(
        (583, 367),
        "cheap observe → confirm → snapshot once",
        font=F_TINY,
        fill=MUTED,
        anchor="mm",
    )

    draw.text((1070, 128), "18.54× retry amp", font=F_METRIC, fill=RED, anchor="mm")
    draw.text((1070, 318), "3.98× retry amp", font=F_METRIC, fill=GREEN, anchor="mm")

    return img


def render_frame(i: int):
    img = draw_base()
    draw = ImageDraw.Draw(img)
    phase = i / FRAMES
    s = phase * SECONDS

    # Top: repeated per-context traffic and rebound.
    for k in range(4):
        local = (phase * 4.0 + k * 0.235) % 1.0

        if local < 0.24:
            moving_dot(img, (207, 195), (301, 195), local / 0.24, RED, 6)
        elif local < 0.66:
            moving_dot(
                img,
                (479, 195),
                (686, 195),
                (local - 0.24) / 0.42,
                RED,
                7,
            )
        elif local < 0.82:
            moving_dot(
                img,
                (884, 195),
                (958, 195),
                (local - 0.66) / 0.16,
                AMBER,
                7,
            )
        else:
            moving_dot(
                img,
                (958, 207),
                (884, 207),
                (local - 0.82) / 0.18,
                RED,
                7,
            )

    pulse = (math.sin(phase * math.tau * 4.0) + 1.0) / 2.0
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    rr = 106 + int(7 * pulse)
    ld.rounded_rectangle(
        (785 - rr, 195 - 57, 785 + rr, 195 + 57),
        radius=24,
        outline=(*RED, 65),
        width=3,
    )
    img.alpha_composite(layer)
    translucent_text(
        img,
        (785, 251),
        "429 / fast-fail / retry",
        F_TINY,
        RED,
        205,
        "mm",
    )

    # Bottom: a single logical recovery progresses through phases.
    if s < 2.0:
        for off in (-22, 0, 22):
            moving_dot(
                img,
                (207, 385 + off * 0.55),
                (301, 385),
                s / 2.0,
                BLUE,
                6,
            )

    elif s < 4.2:
        moving_dot(
            img,
            (479, 385),
            (686, 385),
            (s - 2.0) / 2.2,
            CYAN,
            7,
        )
        translucent_text(img, (585, 413), "4 KiB observe", F_TINY, CYAN, 235, "mm")

    elif s < 5.6:
        moving_dot(
            img,
            (884, 385),
            (958, 385),
            (s - 4.2) / 1.4,
            AMBER,
            7,
        )
        translucent_text(img, (1035, 438), "E / provisional", F_TINY, AMBER, 235, "mm")

    elif s < 7.6:
        moving_dot(
            img,
            (958, 397),
            (884, 397),
            (s - 5.6) / 2.0,
            CYAN,
            7,
        )
        translucent_text(img, (918, 420), "confirm", F_TINY, CYAN, 235, "mm")

    elif s < 9.6:
        moving_dot(
            img,
            (479, 385),
            (686, 385),
            (s - 7.6) / 2.0,
            GREEN,
            8,
        )
        translucent_text(img, (585, 413), "snapshot once", F_TINY, GREEN, 235, "mm")

    else:
        moving_dot(
            img,
            (884, 385),
            (958, 385),
            (s - 9.6) / 2.4,
            GREEN,
            8,
        )
        translucent_text(img, (1035, 438), "H / stable", F_TINY, GREEN, 255, "mm")

    # Bottom service remains calm.
    calm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(calm)
    cd.rounded_rectangle(
        (676, 329, 894, 441),
        radius=24,
        outline=(*GREEN, 34),
        width=3,
    )
    img.alpha_composite(calm)

    footer = "Observe cheaply • suppress duplicates • materialize once • transport ≠ truth"
    draw.text((600, 482), footer, font=F_SMALL, fill=MUTED, anchor="mm")

    return img.convert("P", palette=Image.Palette.ADAPTIVE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="docs/assets/recovery-network.gif",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    frames = [render_frame(i) for i in range(FRAMES)]

    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=False,
        disposal=2,
    )

    print(f"wrote {output} ({len(frames)} frames)")


if __name__ == "__main__":
    main()

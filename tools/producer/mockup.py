from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

CANVAS = (1600, 1200)


def wall(size: tuple[int, int]) -> Image.Image:
    w, h = size
    col = Image.new("L", (1, h))
    for y in range(h):
        col.putpixel((0, y), int(241 - 40 * (y / h)))
    col = col.resize(size)
    light = Image.new("RGB", size, (239, 236, 232))
    dark = Image.new("RGB", size, (206, 201, 196))
    return Image.composite(light, dark, col)


def make_mockup(art_path: str | Path, out_path: str | Path) -> Path:
    width, height = CANVAS
    bg = wall(CANVAS).convert("RGBA")

    art = Image.open(art_path).convert("RGB")
    disp = int(height * 0.60)
    art_r = art.resize((disp, disp), Image.LANCZOS)

    mat, frame = 30, 20
    matted = Image.new("RGB", (disp + 2 * mat, disp + 2 * mat), (250, 249, 247))
    matted.paste(art_r, (mat, mat))
    framed = ImageOps.expand(matted, border=frame, fill=(30, 28, 32))
    fw, fh = framed.size
    fx, fy = (width - fw) // 2, (height - fh) // 2 - 12

    shadow = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", (fw, fh), (0, 0, 0, 115)), (fx + 16, fy + 20))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))

    bg.alpha_composite(shadow)
    bg.alpha_composite(framed.convert("RGBA"), (fx, fy))

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(out, "PNG")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="vapor-studio framed-wall mockup")
    ap.add_argument("art", help="path to the print master PNG")
    ap.add_argument("--out", default=None, help="output file or dir (default <art dir>/mockups/)")
    args = ap.parse_args()

    src = Path(args.art)
    stem = src.stem[:-3] if src.stem.endswith("-4x") else src.stem
    if args.out:
        out = Path(args.out)
        if out.is_dir() or not out.suffix:
            out = out / f"{stem}-mockup.png"
    else:
        out = src.parent / "mockups" / f"{stem}-mockup.png"

    print(make_mockup(src, out))


if __name__ == "__main__":
    main()

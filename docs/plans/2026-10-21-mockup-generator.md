# Mockup Generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Tested, reusable `tools/producer/mockup.py` that turns a print master into a framed-on-a-wall cover image.

**Architecture:** A small Pillow module: a gradient wall + a matted/framed/shadowed composite of the art, with a CLI.

**Tech Stack:** Python 3.11+, Pillow, pytest.

## Global Constraints

- **New dependency:** add `pillow>=10` to `tools/producer/requirements.txt`. (It is already installed in `tools/producer/.venv` from prototyping.)
- Match the approved look exactly (values below). One default, no configurable knobs (YAGNI).
- **ruff clean** (`tools/producer/ruff.toml`). Run tests + lint from repo root with the venv:
  `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/ -v` and `ruff check tools/producer --config tools/producer/ruff.toml`.
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

### Task 1: `mockup.py` module + CLI + tests

**Files:**
- Create: `tools/producer/mockup.py`
- Modify: `tools/producer/requirements.txt` (+ `pillow>=10`)
- Test: `tools/producer/tests/test_mockup.py` (new)

**Interfaces:**
- Produces: `wall(size) -> Image`, `make_mockup(art_path, out_path) -> Path`, `main()` CLI, `CANVAS = (1600, 1200)`.

- [ ] **Step 1: Add Pillow to requirements and confirm it imports**

Append to `tools/producer/requirements.txt`:
```
pillow>=10
```
Confirm (venv already has it): `source tools/producer/.venv/bin/activate && python -c "import PIL; print(PIL.__version__)"`

- [ ] **Step 2: Write the failing tests**

Create `tools/producer/tests/test_mockup.py`:

```python
from PIL import Image

from tools.producer.mockup import CANVAS, make_mockup, wall


def test_wall_returns_rgb_of_given_size():
    img = wall((400, 300))
    assert img.size == (400, 300)
    assert img.mode == "RGB"


def test_make_mockup_writes_valid_canvas_with_art_composited(tmp_path):
    art = tmp_path / "art.png"
    Image.new("RGB", (512, 512), (255, 0, 255)).save(art)  # magenta
    out = make_mockup(art, tmp_path / "m.png")

    assert out.exists()
    img = Image.open(out).convert("RGB")
    assert img.size == CANVAS
    # canvas center falls inside the art region -> should be the magenta art, not wall
    r, g, b = img.getpixel((CANVAS[0] // 2, CANVAS[1] // 2))
    assert r > 150 and b > 150 and g < 120
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/test_mockup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.producer.mockup'`.

- [ ] **Step 4: Write `tools/producer/mockup.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass + full suite + lint**

Run:
```
source tools/producer/.venv/bin/activate
python -m pytest tools/producer/tests/ -v
ruff check tools/producer --config tools/producer/ruff.toml
```
Expected: all pass (existing + 2 new), ruff clean, output pristine.

- [ ] **Step 6: Commit**

```bash
git add tools/producer/mockup.py tools/producer/tests/test_mockup.py tools/producer/requirements.txt
git commit -m "feat(producer): add framed-wall mockup generator

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2 (controller-run): workflow doc + regenerate covers

- [ ] Add the cover step to `docs/workflow.md` Package step (step 6).
- [ ] Regenerate the 16 covers via the real module:
  `for f in pipeline/05-packaged/2026-10-21/*-4x.png; do python -m tools.producer.mockup "$f"; done`

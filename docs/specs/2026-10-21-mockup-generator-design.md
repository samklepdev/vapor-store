# Design — Mockup generator (framed-wall product covers)

**Date:** 2026-10-21
**Status:** Approved (brainstorming → ready for plan)

## 1. Goal

Promote the working mockup prototype into tested, reusable tooling: turn a print
master into a **framed-on-a-wall cover image** for product listings (Gumroad etc.).

## 2. Non-goals (YAGNI)

- No configurable styles/knobs (wall color, frame style, ratio) — one good default.
- No room scenes, perspective warp, or multiple frames — a single centered,
  matted, framed print on a neutral wall.
- Not generative — deterministic image compositing (no ComfyUI).

## 3. Dependency

Adds **Pillow** (`pillow>=10`) to `tools/producer/requirements.txt`. This is the
one place a real imaging library is warranted; the producer is otherwise
stdlib-only. (Already present in the venv from prototyping.)

## 4. Interface

New module `tools/producer/mockup.py`:
- `CANVAS = (1600, 1200)` — 4:3 landscape cover.
- `wall(size: tuple[int, int]) -> PIL.Image.Image` — neutral top-lit gradient wall.
- `make_mockup(art_path, out_path) -> Path` — composite: resized art → white mat →
  dark frame → soft drop shadow → centered on the wall; saves PNG; returns the path.
- `main()` CLI: `python -m tools.producer.mockup <art.png> [--out <path|dir>]`.
  Default output: `<art dir>/mockups/<stem>-mockup.png`, where a trailing `-4x` is
  stripped from the stem (so `bs-x-001-4x.png` → `mockups/bs-x-001-mockup.png`).

## 5. Look (the approved default)

Black frame (`#1E1C20`, 20px) + white mat (`#FAF9F7`, 30px) around the art shown
at 60% of canvas height; soft Gaussian drop shadow; neutral warm-gray gradient wall.

## 6. Testing (TDD, no network)

- `wall((w,h))` returns an RGB image of exactly that size.
- `make_mockup` on a solid-color test art writes a valid **1600×1200** PNG whose
  center region is the art color (not the wall) — proves the art is composited.

## 7. Files

- `tools/producer/mockup.py` (new)
- `tools/producer/requirements.txt` (+ `pillow>=10`)
- `tools/producer/tests/test_mockup.py` (new)
- `docs/workflow.md` — add the cover step to Package (step 6).

## 8. Workflow integration

In the M1 runbook Package step: after upscaling each keeper, generate its cover
with `python -m tools.producer.mockup <master>` → `mockups/` subfolder; use the
cover as the listing's main image.

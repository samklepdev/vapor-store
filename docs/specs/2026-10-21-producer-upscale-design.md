# Design — Producer upscale pass (print resolution)

**Date:** 2026-10-21
**Status:** Approved (brainstorming → ready for plan)
**Depends on:** `ComfyUIProvider` in `tools/producer/providers.py`.

---

## 1. Goal

Turn an **approved draft image** into a **print-resolution** file *without
changing the image* — so the owner's exact Gate-1 picks become sellable wall
art, not regenerated into new images. Upscale runs through the local ComfyUI
server (reusing the existing provider's HTTP seam).

## 2. Non-goals (YAGNI)

- No reshaping to portrait/landscape, no regeneration — the pixels stay the
  same composition, just larger. (Ratio variants = a later step if a niche sells.)
- No multi-ratio/print-size export bundle — that is packaging, handled separately.
- No batch orchestration beyond calling the CLI per file (a shell loop suffices).

## 3. Model

**Real-ESRGAN x4plus** (`RealESRGAN_x4plus.pth`) — **BSD-3-Clause, commercial-safe**.
4× scale: a 1024² pick → **4096²**, which prints crisp to ~27″ at 150 DPI
(standard wall-art density). Lives in ComfyUI's `models/upscale_models/`
(`/Users/sam/ComfyUI-Shared/models/upscale_models/` per the Comfy Desktop
extra-model-paths config).

## 4. Architecture

Extend `ComfyUIProvider` (reuse its `_submit` / `_await_images` / `_download` /
`_open` HTTP seam — no duplication):

- `_upload_image(data: bytes, filename: str) -> str` — `POST /upload/image`
  (multipart/form-data, stdlib-built), returns the uploaded input name.
- `_build_upscale_workflow(image_name: str, model: str, slug: str) -> dict` —
  **pure**. Graph: `LoadImage → UpscaleModelLoader → ImageUpscaleWithModel → SaveImage`.
- `upscale(image: bytes, *, slug: str, model: str) -> bytes` — composes:
  upload → submit(workflow) → await → download (returns the upscaled PNG bytes).

### Upscale workflow graph (ComfyUI API format)

| id | class_type | inputs |
|----|------------|--------|
| 10 | LoadImage | `image = <uploaded name>` |
| 11 | UpscaleModelLoader | `model_name = model` |
| 12 | ImageUpscaleWithModel | `upscale_model = [11,0]`, `image = [10,0]` |
| 13 | SaveImage | `images = [12,0]`, `filename_prefix = slug` |

(IDs 10–13 avoid clashing with the generator workflow's 3–9, for clarity.)

## 5. CLI & config

New module `tools/producer/upscale.py` with `main()`:
```
python -m tools.producer.upscale pipeline/04-approved/<file>.png [--out pipeline/05-packaged/<today>] [--config ...]
```
It loads `[comfyui]` from `config.toml`, builds a `ComfyUIProvider`, reads the
input file, calls `provider.upscale(...)`, and writes `<stem>-4x.png` to the out
dir (default `pipeline/05-packaged/<today>/`, created if missing).

`config.example.toml` `[comfyui]` gains an optional
`upscale_model = "RealESRGAN_x4plus.pth"` (default used if absent).

## 6. Testing (TDD, no server/model needed)

- `_build_upscale_workflow` — pure-function unit test: correct node wiring,
  image name, model, SaveImage prefix.
- `upscale()` composition — monkeypatch `_upload_image` / `_post_json` /
  `_get_json` / `_get_bytes`; assert it uploads, submits the upscale graph, and
  returns the downloaded bytes.
- `_upload_image` — verify it builds a multipart body with the boundary and
  posts to `/upload/image` (monkeypatch the low-level open).
- Reuses the already-tested `_submit`/`_await_images`/`_download` path.

## 7. Files

- `tools/producer/providers.py` — add the three methods to `ComfyUIProvider`.
- `tools/producer/upscale.py` (new) — CLI.
- `tools/producer/config.example.toml` — document `upscale_model`.
- `tools/producer/tests/test_upscale.py` (new) — the tests above.
- Stdlib only; `requirements.txt` unchanged.

## 8. Output & handling

Print masters → `pipeline/05-packaged/<date>/` (already gitignored). The square
is preserved. Owner downloads the Real-ESRGAN model once (setup step).

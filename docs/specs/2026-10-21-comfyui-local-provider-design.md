# Design — Local ComfyUI (SDXL) provider for the producer

**Date:** 2026-10-21
**Status:** Approved (brainstorming → ready for plan)
**Depends on:** the generator-agnostic producer in `tools/producer/` (Task 4,
commit `0ac8124`) and its `Provider` protocol.

---

## 1. Goal

Add a **free, local, resale-license-clean** image backend to the producer so
image generation can run on the owner's own machine with no per-image API cost
and no third-party ToS exposure — as an alternative to the paid `FluxFalProvider`.

The backend is **ComfyUI** (local HTTP server, default `http://127.0.0.1:8188`)
driving **SDXL** (CreativeML OpenRAIL-M — commercial use permitted).

## 2. Non-goals (YAGNI for v1)

- No LoRA loading, img2img, inpainting, or SDXL refiner pass. Text-to-image only.
- No ComfyUI installation/model-download automation — the owner installs ComfyUI
  and the SDXL checkpoint themselves (multi-GB, machine-specific).
- No new OpenClaw skill. This is **M0 producer tooling**; the M2 skill that wraps
  the producer stays deferred until a niche sells (Task 8 gate).
- No auto-discovery of checkpoints. The checkpoint filename is config.

## 3. Architecture

A new `ComfyUIProvider` in `tools/producer/providers.py` implementing the
existing `Provider` protocol:

```python
class ComfyUIProvider:
    name = "comfyui-sdxl"
    def __init__(self, base_url: str, checkpoint: str, *, steps: int = 30,
                 cfg: float = 7.0, sampler: str = "euler",
                 scheduler: str = "normal", negative: str = "") -> None: ...
    def generate(self, req: GenRequest) -> list[bytes]: ...
```

`run`, `save_batch`, `dated_output_dir`, and the CLI orchestration are
**unchanged** — the generator-agnostic seam is the whole point. `FluxFalProvider`
remains a selectable backend.

### Network isolation (mirrors `FluxFalProvider._submit`/`_download`)

The HTTP interaction with ComfyUI lives in private methods so orchestration stays
testable with the existing `FakeProvider`:

- `_build_workflow(req) -> dict` — **pure function**, no I/O. Builds the SDXL
  text-to-image graph (ComfyUI API/"prompt" format) from the request.
- `_submit(graph) -> str` — `POST /prompt` with `{"prompt": graph, "client_id": <uuid>}`; returns `prompt_id`.
- `_await_images(prompt_id) -> list[dict]` — poll `GET /history/{prompt_id}` until
  the entry appears with outputs; return the image refs
  (`{filename, subfolder, type}`) from the SaveImage node's outputs.
- `_download(ref) -> bytes` — `GET /view?filename=&subfolder=&type=output` → PNG bytes.

`generate` composes: `_download(ref) for ref in _await_images(_submit(_build_workflow(req)))`.

### SDXL workflow graph (text-to-image, API format)

Nodes `_build_workflow` emits (ComfyUI "prompt" API JSON, node ids are strings):

| id | class_type | inputs driven by request/config |
|----|------------|---------------------------------|
| 4 | CheckpointLoaderSimple | `ckpt_name = checkpoint` |
| 6 | CLIPTextEncode (positive) | `text = req.prompt`, `clip = [4,1]` |
| 7 | CLIPTextEncode (negative) | `text = negative`, `clip = [4,1]` |
| 5 | EmptyLatentImage | `width = req.width`, `height = req.height`, `batch_size = req.n` |
| 3 | KSampler | `seed` (random), `steps`, `cfg`, `sampler_name`, `scheduler`, `denoise=1.0`, `model=[4,0]`, `positive=[6,0]`, `negative=[7,0]`, `latent_image=[5,0]` |
| 8 | VAEDecode | `samples=[3,0]`, `vae=[4,2]` |
| 9 | SaveImage | `images=[8,0]`, `filename_prefix=req.slug` |

`batch_size = req.n` makes a single prompt produce all N images.

## 4. Config & provider selection

`config.toml` / `config.example.toml` gain a selector and a ComfyUI section;
`[fal]` is unchanged:

```toml
[provider]
kind = "comfyui"   # "comfyui" | "flux-fal"

[comfyui]
base_url = "http://127.0.0.1:8188"
checkpoint = "sd_xl_base_1.0.safetensors"   # the file you dropped in models/checkpoints/

[fal]
api_key = "PASTE_FAL_KEY_HERE"
model = "fal-ai/flux/dev"
```

`config.example.toml` carries a **license note**: local generation must use a
commercially-licensed checkpoint (SDXL / FLUX.1-schnell); **never run FLUX.1-dev
locally for resale** (non-commercial weights license).

In `generate.py`, replace `_load_fal` with `_load_provider(cfg) -> Provider`:
- read `cfg["provider"]["kind"]` (default `"flux-fal"` for backward compatibility)
- `comfyui` → build `ComfyUIProvider` from `cfg["comfyui"]`
- `flux-fal` → build `FluxFalProvider` from `cfg["fal"]` (existing path)

Add a `--provider {comfyui,flux-fal}` CLI flag that overrides the config `kind`.

## 5. Error handling (fail loud, clear messages)

- ComfyUI unreachable (connection refused) → `RuntimeError` naming the base_url
  and the hint that ComfyUI must be running.
- `POST /prompt` returns a node-validation error (e.g. unknown checkpoint) →
  surface ComfyUI's error body.
- History entry reports an execution error → raise with the reported error.
- Zero images in outputs → raise (never silently write zero files), consistent
  with the fal fix in `dd4d293`.
- Polling has a bounded timeout (configurable, default generous for local GPU).

## 6. Testing strategy (TDD, no GPU/server required)

1. **Orchestration** — existing `FakeProvider` tests in `test_generate.py`
   unchanged; still green.
2. **`_build_workflow`** — pure-function unit tests: a `GenRequest(prompt, width,
   height, n, slug)` + checkpoint maps to the right node inputs (positive text,
   EmptyLatentImage width/height/batch_size, checkpoint name, SaveImage prefix).
3. **Response parsing** — `_await_images` / `_download` tested against a **mocked
   HTTP transport** (fake `/history` payload and `/view` bytes): verify it returns
   the right ordered PNG bytes and raises on error/empty payloads.
4. **Provider selection** — `_load_provider` returns the correct concrete type for
   each `kind` and honors the CLI override.
5. **Live smoke test** — one manual run against the real ComfyUI server once it's
   up (the local equivalent of fal's Step 6): generate 2 images, confirm PNGs land
   under `pipeline/02-raw/<today>/`.

## 7. Files touched

- `tools/producer/providers.py` — add `ComfyUIProvider` (+ `_build_workflow`).
- `tools/producer/generate.py` — `_load_provider` factory + `--provider` flag.
- `tools/producer/config.example.toml` — `[provider]`, `[comfyui]`, license note.
- `tools/producer/tests/test_providers.py` (new) — workflow builder + response
  parsing + selection tests.

**No new dependency.** The ComfyUI HTTP calls use the stdlib (`urllib.request`
for GET/POST + `json`), matching `FluxFalProvider._download` and this project's
zero-dependency posture. `requirements.txt` is unchanged. Tests mock at the
`urllib`/transport boundary so no server is needed.

## 8. Open item (resolved at build time, not blocking)

Exact SDXL **checkpoint filename** the owner installs into ComfyUI's
`models/checkpoints/`. It is a config value (`[comfyui].checkpoint`), so no code
change is needed when it's known.

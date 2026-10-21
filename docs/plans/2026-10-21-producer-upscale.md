# Producer Upscale Pass — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a reusable ComfyUI upscale pass so an approved draft image becomes a print-resolution file (Real-ESRGAN x4plus, 4×) without changing the image.

**Architecture:** Extend `ComfyUIProvider` with upload + upscale-workflow + `upscale()`, reusing its existing HTTP seam; add a thin `upscale.py` CLI. TDD with a monkeypatched transport.

**Tech Stack:** Python 3.11+, stdlib only (`urllib`, `json`, `uuid`), pytest.

## Global Constraints

- **Zero new dependencies.** Stdlib `urllib`/`json`/`uuid` only; `requirements.txt` unchanged.
- **Reuse, don't duplicate** the HTTP seam: `upscale()` must go through the existing `_submit` / `_await_images` / `_download` / `_open`. Do not copy that logic.
- **Do not change** `GenRequest`, the `Provider` protocol, `FluxFalProvider`, or `ComfyUIProvider.generate` / `_build_workflow`.
- **Model:** `RealESRGAN_x4plus.pth` (BSD-3, commercial-safe), 4×. Default model name is a parameter, not hardcoded in logic beyond the default value.
- **ruff clean** (`tools/producer/ruff.toml`). Run tests + lint from repo root with the venv:
  `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/ -v` and `ruff check tools/producer --config tools/producer/ruff.toml`.
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

### Task 1: Upscale methods on `ComfyUIProvider` + `upscale.py` CLI

**Files:**
- Modify: `tools/producer/providers.py` (add three methods to `ComfyUIProvider`)
- Create: `tools/producer/upscale.py`
- Modify: `tools/producer/config.example.toml` (document `upscale_model`)
- Test: `tools/producer/tests/test_upscale.py` (new)

**Interfaces:**
- Consumes: `ComfyUIProvider` HTTP seam (`_submit`, `_await_images`, `_download`, `_open`) and `base_url`.
- Produces:
  - `ComfyUIProvider._upload_image(data: bytes, filename: str) -> str`
  - `ComfyUIProvider._build_upscale_workflow(image_name: str, model: str, slug: str) -> dict`
  - `ComfyUIProvider.upscale(image: bytes, *, slug: str = "upscaled", model: str = "RealESRGAN_x4plus.pth") -> bytes`
  - `tools/producer/upscale.py` with `main()` (CLI).

- [ ] **Step 1: Write the failing tests**

Create `tools/producer/tests/test_upscale.py`:

```python
import json

from tools.producer.providers import ComfyUIProvider


def _provider() -> ComfyUIProvider:
    return ComfyUIProvider("http://127.0.0.1:8188", "sd_xl_base_1.0.safetensors", poll_interval=0.0)


def test_build_upscale_workflow_wiring():
    p = _provider()
    g = p._build_upscale_workflow("input.png", "RealESRGAN_x4plus.pth", "bs-night-neon-001")
    assert g["10"]["class_type"] == "LoadImage"
    assert g["10"]["inputs"]["image"] == "input.png"
    assert g["11"]["class_type"] == "UpscaleModelLoader"
    assert g["11"]["inputs"]["model_name"] == "RealESRGAN_x4plus.pth"
    assert g["12"]["class_type"] == "ImageUpscaleWithModel"
    assert g["12"]["inputs"]["upscale_model"] == ["11", 0]
    assert g["12"]["inputs"]["image"] == ["10", 0]
    assert g["13"]["class_type"] == "SaveImage"
    assert g["13"]["inputs"]["images"] == ["12", 0]
    assert g["13"]["inputs"]["filename_prefix"] == "bs-night-neon-001"


def test_upscale_uploads_submits_and_downloads(monkeypatch):
    p = _provider()
    seen = {}

    def fake_upload(data, filename):
        seen["uploaded"] = (data, filename)
        return "input.png"

    def fake_post(path, payload):
        seen["submit_path"] = path
        seen["graph"] = payload["prompt"]
        return {"prompt_id": "pid"}

    history = {
        "pid": {
            "status": {"status_str": "success", "completed": True},
            "outputs": {"13": {"images": [{"filename": "up.png", "subfolder": "", "type": "output"}]}},
        }
    }
    monkeypatch.setattr(p, "_upload_image", fake_upload)
    monkeypatch.setattr(p, "_post_json", fake_post)
    monkeypatch.setattr(p, "_get_json", lambda path: history)
    monkeypatch.setattr(p, "_get_bytes", lambda path: b"UP:" + path.encode())

    out = p.upscale(b"rawbytes", slug="bs", model="RealESRGAN_x4plus.pth")

    assert seen["uploaded"] == (b"rawbytes", "bs.png")
    assert seen["submit_path"] == "/prompt"
    assert seen["graph"]["11"]["inputs"]["model_name"] == "RealESRGAN_x4plus.pth"
    assert out == b"UP:/view?filename=up.png&subfolder=&type=output"


def test_upload_image_builds_multipart(monkeypatch):
    p = _provider()
    captured = {}

    def fake_open(request):
        captured["url"] = request.full_url
        captured["ctype"] = request.headers.get("Content-type")
        captured["body"] = request.data
        return json.dumps({"name": "input.png", "subfolder": "", "type": "input"}).encode()

    monkeypatch.setattr(p, "_open", fake_open)
    name = p._upload_image(b"PNGDATA", "bs.png")

    assert name == "input.png"
    assert captured["url"].endswith("/upload/image")
    assert "multipart/form-data; boundary=" in captured["ctype"]
    assert b'name="image"; filename="bs.png"' in captured["body"]
    assert b"PNGDATA" in captured["body"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/test_upscale.py -v`
Expected: FAIL — `AttributeError: 'ComfyUIProvider' object has no attribute '_build_upscale_workflow'`.

- [ ] **Step 3: Add the three methods to `ComfyUIProvider`**

In `tools/producer/providers.py`, add these methods inside `ComfyUIProvider`
(e.g. after `_download`, before the `_post_json`/`_get_json` HTTP helpers):

```python
    def upscale(
        self,
        image: bytes,
        *,
        slug: str = "upscaled",
        model: str = "RealESRGAN_x4plus.pth",
    ) -> bytes:
        name = self._upload_image(image, f"{slug}.png")
        prompt_id = self._submit(self._build_upscale_workflow(name, model, slug))
        refs = self._await_images(prompt_id)
        return self._download(refs[0])

    def _build_upscale_workflow(self, image_name: str, model: str, slug: str) -> dict:
        return {
            "10": {"class_type": "LoadImage", "inputs": {"image": image_name}},
            "11": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": model}},
            "12": {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {"upscale_model": ["11", 0], "image": ["10", 0]},
            },
            "13": {
                "class_type": "SaveImage",
                "inputs": {"images": ["12", 0], "filename_prefix": slug},
            },
        }

    def _upload_image(self, data: bytes, filename: str) -> str:
        boundary = uuid.uuid4().hex
        body = b"".join(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode(),
                b"Content-Type: image/png\r\n\r\n",
                data,
                f"\r\n--{boundary}--\r\n".encode(),
            ]
        )
        request = urllib.request.Request(
            self._base_url + "/upload/image",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        resp = json.loads(self._open(request))
        name = resp.get("name")
        if not name:
            raise RuntimeError(f"ComfyUI /upload/image returned no name: {resp}")
        subfolder = resp.get("subfolder")
        return f"{subfolder}/{name}" if subfolder else name
```

(`uuid`, `json`, `urllib.request` are already imported at the top of the file.)

- [ ] **Step 4: Create `tools/producer/upscale.py`**

```python
from __future__ import annotations

import argparse
import datetime as dt
import tomllib
from pathlib import Path

from .providers import ComfyUIProvider


def main() -> None:
    ap = argparse.ArgumentParser(description="vapor-studio image upscaler (ComfyUI)")
    ap.add_argument("image", help="path to the approved PNG to upscale")
    ap.add_argument("--config", default="tools/producer/config.toml")
    ap.add_argument("--out", default=None, help="output dir (default pipeline/05-packaged/<today>)")
    args = ap.parse_args()

    cfg = tomllib.loads(Path(args.config).read_text())["comfyui"]
    provider = ComfyUIProvider(base_url=cfg["base_url"], checkpoint=cfg.get("checkpoint", ""))
    model = cfg.get("upscale_model", "RealESRGAN_x4plus.pth")

    src = Path(args.image)
    out_dir = (
        Path(args.out) if args.out else Path("pipeline/05-packaged") / dt.date.today().isoformat()
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    data = provider.upscale(src.read_bytes(), slug=src.stem, model=model)
    out = out_dir / f"{src.stem}-4x.png"
    out.write_bytes(data)
    print(out)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests to verify they pass + full suite + lint**

Run:
```
source tools/producer/.venv/bin/activate
python -m pytest tools/producer/tests/ -v
ruff check tools/producer --config tools/producer/ruff.toml
```
Expected: all tests pass (existing + 3 new), ruff clean, output pristine.

- [ ] **Step 6: Update `config.example.toml`**

Add the optional upscale model line inside the `[comfyui]` table:
```toml
# Optional: upscale model in ComfyUI's models/upscale_models/ (BSD-3, resale-safe).
upscale_model = "RealESRGAN_x4plus.pth"
```

- [ ] **Step 7: Commit**

```bash
git add tools/producer/providers.py tools/producer/upscale.py \
  tools/producer/tests/test_upscale.py tools/producer/config.example.toml
git commit -m "feat(producer): add ComfyUI upscale pass (Real-ESRGAN x4)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2 (owner/controller-run): download model + live upscale smoke

Not agent-unit-testable — needs the model file + running ComfyUI.

- [ ] Download `RealESRGAN_x4plus.pth` (~64MB, BSD-3) to `/Users/sam/ComfyUI-Shared/models/upscale_models/` from
  `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth`.
- [ ] Confirm ComfyUI lists it: `GET /object_info/UpscaleModelLoader` → `model_name` options include it (loopback needs the sandbox override).
- [ ] Live smoke on one approved pick:
  ```
  source tools/producer/.venv/bin/activate
  python -m tools.producer.upscale pipeline/04-approved/bs-night-neon-001.png
  ```
  Expected: a `*-4x.png` (~4096²) printed under `pipeline/05-packaged/<today>/`; verify dimensions. If the ComfyUI node names differ in this version, adjust `_build_upscale_workflow` and re-run Task 1 tests.

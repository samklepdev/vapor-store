# Local ComfyUI (SDXL) Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a free, local, resale-license-clean image backend (`ComfyUIProvider`, SDXL via a local ComfyUI server) to the producer, selectable alongside the existing paid fal.ai backend.

**Architecture:** A new `ComfyUIProvider` implements the existing `Provider` protocol, so `run`/`save_batch`/CLI are unchanged. It builds a standard SDXL text-to-image workflow graph, submits it to ComfyUI's HTTP API, polls for completion, and downloads the resulting PNG bytes. A config-driven factory picks the provider; a `--provider` flag overrides.

**Tech Stack:** Python 3.11+, stdlib only (`urllib.request`, `urllib.parse`, `json`), pytest. No new dependencies.

## Global Constraints

- **Zero new dependencies.** ComfyUI HTTP uses stdlib `urllib`/`json` only. `requirements.txt` is unchanged.
- **Stable public interface.** Do not change `GenRequest` or the `Provider` protocol — the M2 skill depends on them.
- **Resale-license-clean.** Local generation must use a commercially-licensed checkpoint (SDXL / FLUX.1-schnell). `config.example.toml` must warn: never run FLUX.1-dev locally for resale.
- **Python target py311**; code runs on the repo's Python 3.15 venv at `tools/producer/.venv`.
- **ruff clean** (`tools/producer/ruff.toml`: line-length 100, select E, F, I, UP).
- **Run tests and lint from the repo root** (`/Users/sam/Projects/ai/vapor-studio`) with the venv activated, so the `tools.producer` package resolves:
  `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/ -v` and `ruff check tools/producer --config tools/producer/ruff.toml`.
- **Commit trailer:** end every commit message with
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- `providers.py` already starts with `from __future__ import annotations` — keep it; use `list[...]`/`dict[...]` builtins (UP rule).

---

### Task 1: `ComfyUIProvider` — workflow builder + ComfyUI HTTP client

**Files:**
- Modify: `tools/producer/providers.py` (append the new class; do not touch `GenRequest`, `Provider`, or `FluxFalProvider`)
- Test: `tools/producer/tests/test_providers.py` (new)

**Interfaces:**
- Consumes: `GenRequest` (from `tools/producer/providers.py`): `prompt: str, width=1024, height=1024, n=1, slug="img"`.
- Produces:
  - `ComfyUIProvider(base_url: str, checkpoint: str, *, steps: int = 30, cfg: float = 7.0, sampler: str = "euler", scheduler: str = "normal", negative: str = "", poll_interval: float = 1.0, timeout: float = 600.0)` with class attr `name = "comfyui-sdxl"`, implementing `Provider`.
  - `ComfyUIProvider.generate(req: GenRequest) -> list[bytes]`
  - `ComfyUIProvider._build_workflow(req: GenRequest, seed: int) -> dict` (pure)
  - Transport seam methods `_post_json(path, payload) -> dict`, `_get_json(path) -> dict`, `_get_bytes(path) -> bytes` (monkeypatched in tests).

- [ ] **Step 1: Write the failing tests**

Create `tools/producer/tests/test_providers.py`:

```python
import pytest

from tools.producer.providers import ComfyUIProvider, GenRequest, Provider


def _provider() -> ComfyUIProvider:
    return ComfyUIProvider(
        "http://127.0.0.1:8188/", "sd_xl_base_1.0.safetensors", poll_interval=0.0
    )


def test_satisfies_provider_protocol():
    assert isinstance(_provider(), Provider)
    assert _provider().name == "comfyui-sdxl"


def test_build_workflow_maps_request_fields():
    p = _provider()
    req = GenRequest(prompt="chrome grid sunset", width=1152, height=896, n=3, slug="bs")
    g = p._build_workflow(req, seed=42)

    assert g["4"]["inputs"]["ckpt_name"] == "sd_xl_base_1.0.safetensors"
    assert g["6"]["inputs"]["text"] == "chrome grid sunset"      # positive prompt
    assert g["6"]["inputs"]["clip"] == ["4", 1]
    assert g["7"]["inputs"]["text"] == ""                        # negative (default)
    assert g["5"]["inputs"] == {"width": 1152, "height": 896, "batch_size": 3}
    assert g["3"]["inputs"]["seed"] == 42
    assert g["3"]["inputs"]["steps"] == 30
    assert g["3"]["inputs"]["model"] == ["4", 0]
    assert g["3"]["inputs"]["latent_image"] == ["5", 0]
    assert g["8"]["inputs"]["samples"] == ["3", 0]
    assert g["9"]["inputs"]["filename_prefix"] == "bs"


def test_generate_submits_awaits_and_downloads_in_order(monkeypatch):
    p = _provider()
    sent = {}
    history = {
        "pid": {
            "status": {"status_str": "success", "completed": True},
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "a.png", "subfolder": "", "type": "output"},
                        {"filename": "b.png", "subfolder": "sub", "type": "output"},
                    ]
                }
            },
        }
    }
    monkeypatch.setattr(p, "_post_json", lambda path, payload: sent.update(path=path, payload=payload) or {"prompt_id": "pid"})
    monkeypatch.setattr(p, "_get_json", lambda path: history)
    monkeypatch.setattr(p, "_get_bytes", lambda path: b"BYTES:" + path.encode())

    out = p.generate(GenRequest(prompt="x", n=2, slug="s"))

    assert sent["path"] == "/prompt"
    assert "prompt" in sent["payload"] and "client_id" in sent["payload"]
    assert out == [
        b"BYTES:/view?filename=a.png&subfolder=&type=output",
        b"BYTES:/view?filename=b.png&subfolder=sub&type=output",
    ]


def test_generate_raises_when_prompt_rejected(monkeypatch):
    p = _provider()
    monkeypatch.setattr(p, "_post_json", lambda path, payload: {"error": "bad node"})
    with pytest.raises(RuntimeError, match="rejected"):
        p.generate(GenRequest(prompt="x", n=1, slug="s"))


def test_generate_raises_when_no_images(monkeypatch):
    p = _provider()
    history = {"pid": {"status": {"status_str": "success", "completed": True}, "outputs": {}}}
    monkeypatch.setattr(p, "_post_json", lambda path, payload: {"prompt_id": "pid"})
    monkeypatch.setattr(p, "_get_json", lambda path: history)
    with pytest.raises(RuntimeError, match="no images"):
        p.generate(GenRequest(prompt="x", n=1, slug="s"))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/test_providers.py -v`
Expected: FAIL — `ImportError: cannot import name 'ComfyUIProvider'`.

- [ ] **Step 3: Implement `ComfyUIProvider`**

Append to `tools/producer/providers.py` (after `FluxFalProvider`). The three
top-of-file imports (`import json`, `import time`, and `import urllib.request`,
`urllib.error`, `urllib.parse`) go with the existing imports — note
`FluxFalProvider._download` already imports `urllib.request` locally; keep that
as-is and add module-level imports for the new class:

```python
class ComfyUIProvider:
    """SDXL text-to-image via a local ComfyUI server (resale-license-clean).

    The HTTP calls live in `_post_json`/`_get_json`/`_get_bytes` so the
    orchestration is testable by monkeypatching that seam. `_build_workflow`
    is pure (no I/O) and unit-tested directly."""

    name = "comfyui-sdxl"

    def __init__(
        self,
        base_url: str,
        checkpoint: str,
        *,
        steps: int = 30,
        cfg: float = 7.0,
        sampler: str = "euler",
        scheduler: str = "normal",
        negative: str = "",
        poll_interval: float = 1.0,
        timeout: float = 600.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._checkpoint = checkpoint
        self._steps = steps
        self._cfg = cfg
        self._sampler = sampler
        self._scheduler = scheduler
        self._negative = negative
        self._poll_interval = poll_interval
        self._timeout = timeout
        self._client_id = str(uuid.uuid4())

    def generate(self, req: GenRequest) -> list[bytes]:
        seed = random.randint(0, 2**63 - 1)
        prompt_id = self._submit(self._build_workflow(req, seed))
        refs = self._await_images(prompt_id)
        return [self._download(ref) for ref in refs]

    def _build_workflow(self, req: GenRequest, seed: int) -> dict:
        return {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": self._checkpoint},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": req.prompt, "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": self._negative, "clip": ["4", 1]},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": req.width, "height": req.height, "batch_size": req.n},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": self._steps,
                    "cfg": self._cfg,
                    "sampler_name": self._sampler,
                    "scheduler": self._scheduler,
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"images": ["8", 0], "filename_prefix": req.slug},
            },
        }

    def _submit(self, graph: dict) -> str:
        resp = self._post_json("/prompt", {"prompt": graph, "client_id": self._client_id})
        prompt_id = resp.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"ComfyUI /prompt rejected the workflow: {resp}")
        return prompt_id

    def _await_images(self, prompt_id: str) -> list[dict]:
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            entry = self._get_json(f"/history/{prompt_id}").get(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise RuntimeError(f"ComfyUI execution error: {status}")
                refs = [
                    img
                    for node_out in entry.get("outputs", {}).values()
                    for img in node_out.get("images", [])
                ]
                if refs:
                    return refs
                if status.get("completed"):
                    raise RuntimeError("ComfyUI finished with no images")
            time.sleep(self._poll_interval)
        raise RuntimeError(f"ComfyUI timed out after {self._timeout}s for prompt {prompt_id}")

    def _download(self, ref: dict) -> bytes:
        query = urllib.parse.urlencode(
            {
                "filename": ref["filename"],
                "subfolder": ref.get("subfolder", ""),
                "type": ref.get("type", "output"),
            }
        )
        return self._get_bytes(f"/view?{query}")

    def _post_json(self, path: str, payload: dict) -> dict:
        request = urllib.request.Request(
            self._base_url + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._read_json(request)

    def _get_json(self, path: str) -> dict:
        return self._read_json(urllib.request.Request(self._base_url + path))

    def _read_json(self, request: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(request) as resp:  # noqa: S310 (local trusted URL)
                return json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"ComfyUI unreachable at {self._base_url} (is the server running?): {exc}"
            ) from exc

    def _get_bytes(self, path: str) -> bytes:
        try:
            with urllib.request.urlopen(self._base_url + path) as resp:  # noqa: S310
                return resp.read()
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"ComfyUI unreachable at {self._base_url} (is the server running?): {exc}"
            ) from exc
```

The top-of-file import block must end up exactly like this (ruff's I rule
orders plain `import` statements before `from` imports within the stdlib
group). Replace the existing import block with:

```python
from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
```

(`FluxFalProvider._download` keeps its local `import urllib.request` — a
redundant-but-valid local import; ruff does not flag it.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/test_providers.py -v`
Expected: PASS — 5 passed.

- [ ] **Step 5: Lint**

Run: `ruff check tools/producer --config tools/producer/ruff.toml`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add tools/producer/providers.py tools/producer/tests/test_providers.py
git commit -m "feat(producer): add local ComfyUI SDXL provider

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Provider selection — factory, `--provider` flag, config template

**Files:**
- Modify: `tools/producer/generate.py` (replace `_load_fal` with `_load_provider`; add `--provider` arg)
- Modify: `tools/producer/config.example.toml` (add `[provider]` + `[comfyui]` + license note)
- Test: `tools/producer/tests/test_generate.py` (add selection tests)

**Interfaces:**
- Consumes: `FluxFalProvider`, `ComfyUIProvider`, `Provider` from `tools/producer/providers.py` (Task 1).
- Produces: `_load_provider(cfg: dict, override: str | None = None) -> Provider` in `generate.py`; CLI gains `--provider {comfyui,flux-fal}`.

- [ ] **Step 1: Write the failing selection tests**

Add to `tools/producer/tests/test_generate.py` (add `import pytest` at the top if absent, and extend the existing import from `tools.producer.generate`):

```python
import pytest

from tools.producer.generate import _load_provider
from tools.producer.providers import ComfyUIProvider, FluxFalProvider


def test_load_provider_defaults_to_fal():
    cfg = {"fal": {"api_key": "k"}}
    assert isinstance(_load_provider(cfg), FluxFalProvider)


def test_load_provider_comfyui_from_config():
    cfg = {
        "provider": {"kind": "comfyui"},
        "comfyui": {"base_url": "http://127.0.0.1:8188", "checkpoint": "c.safetensors"},
    }
    p = _load_provider(cfg)
    assert isinstance(p, ComfyUIProvider)
    assert p.name == "comfyui-sdxl"


def test_cli_override_beats_config_kind():
    cfg = {
        "provider": {"kind": "flux-fal"},
        "fal": {"api_key": "k"},
        "comfyui": {"base_url": "http://127.0.0.1:8188", "checkpoint": "c.safetensors"},
    }
    assert isinstance(_load_provider(cfg, override="comfyui"), ComfyUIProvider)


def test_unknown_provider_kind_raises():
    with pytest.raises(ValueError, match="unknown provider"):
        _load_provider({"provider": {"kind": "nope"}})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/test_generate.py -v`
Expected: FAIL — `ImportError: cannot import name '_load_provider'`.

- [ ] **Step 3: Replace `_load_fal` with `_load_provider` and add the CLI flag**

In `tools/producer/generate.py`, change the import line to add `ComfyUIProvider`:

```python
from .providers import ComfyUIProvider, FluxFalProvider, GenRequest, Provider
```

Delete the existing `_load_fal` function and replace it with:

```python
def _load_provider(cfg: dict, override: str | None = None) -> Provider:
    kind = override or cfg.get("provider", {}).get("kind", "flux-fal")
    if kind == "comfyui":
        c = cfg["comfyui"]
        return ComfyUIProvider(base_url=c["base_url"], checkpoint=c["checkpoint"])
    if kind == "flux-fal":
        f = cfg["fal"]
        return FluxFalProvider(api_key=f["api_key"], model=f.get("model", "fal-ai/flux/dev"))
    raise ValueError(f"unknown provider kind: {kind!r}")
```

In `main()`, add the flag (after the `--config` argument) and switch the
provider construction. Replace these two lines:

```python
    provider = _load_fal(Path(args.config))
```

with:

```python
    cfg = tomllib.loads(Path(args.config).read_text())
    provider = _load_provider(cfg, args.provider)
```

and add this argument alongside the others in `main()`:

```python
    ap.add_argument("--provider", choices=["comfyui", "flux-fal"], default=None,
                    help="override [provider].kind from config")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `source tools/producer/.venv/bin/activate && python -m pytest tools/producer/tests/ -v`
Expected: PASS — all tests (orchestration + provider + selection) green.

- [ ] **Step 5: Update `config.example.toml`**

Replace the contents of `tools/producer/config.example.toml` with:

```toml
# Producer configuration. Copy to config.toml and fill in. config.toml is gitignored.

[provider]
# Which backend generate.py uses: "comfyui" (local, free) or "flux-fal" (paid API).
kind = "comfyui"

[comfyui]
# Local ComfyUI server. Start ComfyUI, then point this at it.
base_url = "http://127.0.0.1:8188"
# The checkpoint file in ComfyUI's models/checkpoints/.
# LICENSE: local generation for resale must use a commercially-licensed model
# (SDXL / FLUX.1-schnell). NEVER run FLUX.1-dev locally for resale (non-commercial weights).
checkpoint = "sd_xl_base_1.0.safetensors"

[fal]
# Only used when provider.kind = "flux-fal". Paid per image.
api_key = "PASTE_FAL_KEY_HERE"
model = "fal-ai/flux/dev"
```

- [ ] **Step 6: Lint**

Run: `ruff check tools/producer --config tools/producer/ruff.toml`
Expected: `All checks passed!`

- [ ] **Step 7: Commit**

```bash
git add tools/producer/generate.py tools/producer/tests/test_generate.py tools/producer/config.example.toml
git commit -m "feat(producer): config-driven provider selection (comfyui | flux-fal)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3 (owner-run, not agent-executable): live ComfyUI smoke test

Equivalent of fal's Step 6 — run once when ComfyUI is up with the SDXL
checkpoint installed. Not automated (needs the running server + model weights).

- [ ] Start ComfyUI and confirm `http://127.0.0.1:8188` is reachable.
- [ ] Set `[comfyui].checkpoint` in `config.toml` to the exact filename in `models/checkpoints/`.
- [ ] Run:
  ```bash
  source tools/producer/.venv/bin/activate
  python -m tools.producer.generate --niche battlestation \
    --prompt "retro-futurist chrome grid, sunset gradient, original art" --n 2
  ```
- [ ] Expected: two PNG paths printed under `pipeline/02-raw/<today>/`; open them to confirm they render. If the history/output shape differs from this ComfyUI version, adjust `_await_images`/`_download` and re-run the Task 1 tests.

---

## Notes for the executor

- Tasks 1 and 2 are agent-executable and independently reviewable. Task 3 is owner-run.
- This is M0 producer tooling. Do NOT build an M2 OpenClaw skill wrapping it — that stays deferred until a niche sells (vapor-studio spec, Task 8 gate).

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


@dataclass
class GenRequest:
    prompt: str
    width: int = 1024
    height: int = 1024
    n: int = 1
    slug: str = "img"


@runtime_checkable
class Provider(Protocol):
    name: str

    def generate(self, req: GenRequest) -> list[bytes]:
        """Return `req.n` images as raw PNG bytes."""
        ...


class FluxFalProvider:
    """Flux via fal.ai. The network call is isolated in `_submit`/`_download`
    so the orchestration in generate.py can be tested with a fake provider.

    NOTE: confirm the exact fal-client call and response shape against current
    fal.ai docs during execution (network code, not unit-tested here)."""

    name = "flux-fal"

    def __init__(self, api_key: str, model: str = "fal-ai/flux/dev") -> None:
        self._api_key = api_key
        self._model = model

    def generate(self, req: GenRequest) -> list[bytes]:
        urls = self._submit(req)
        return [self._download(u) for u in urls]

    def _submit(self, req: GenRequest) -> list[str]:
        import os

        import fal_client

        # Config-loaded key always wins; setdefault would silently honor a
        # stale FAL_KEY left in the environment instead of config.toml.
        os.environ["FAL_KEY"] = self._api_key
        result = fal_client.subscribe(
            self._model,
            arguments={
                "prompt": req.prompt,
                "image_size": {"width": req.width, "height": req.height},
                "num_images": req.n,
            },
        )
        # Python fal_client returns top-level `images`; some fal responses nest
        # under `data`. Accept either and fail loudly rather than silently
        # producing zero files on an unexpected shape.
        images = result.get("images") or result.get("data", {}).get("images")
        if not images:
            raise RuntimeError(f"fal response had no images; keys={list(result)}")
        return [img["url"] for img in images]

    def _download(self, url: str) -> bytes:
        import urllib.request

        with urllib.request.urlopen(url) as resp:  # noqa: S310 (trusted fal URL)
            return resp.read()


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
        request_timeout: float = 30.0,
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
        self._request_timeout = request_timeout
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
            with urllib.request.urlopen(request, timeout=self._request_timeout) as resp:  # noqa: S310 (local trusted URL)
                return json.loads(resp.read())
        except (urllib.error.URLError, TimeoutError) as exc:
            msg = (
                f"ComfyUI unreachable or unresponsive at {self._base_url} "
                f"(is the server running?): {exc}"
            )
            raise RuntimeError(msg) from exc

    def _get_bytes(self, path: str) -> bytes:
        try:
            url = self._base_url + path
            with urllib.request.urlopen(url, timeout=self._request_timeout) as resp:  # noqa: S310
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            msg = (
                f"ComfyUI unreachable or unresponsive at {self._base_url} "
                f"(is the server running?): {exc}"
            )
            raise RuntimeError(msg) from exc

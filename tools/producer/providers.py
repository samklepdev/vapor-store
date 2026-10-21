from __future__ import annotations

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
